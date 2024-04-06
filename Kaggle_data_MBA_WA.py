# Importing libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import datetime as dt
import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore")

# Runtime Configuration Parameters for Matplotlib
plt.rcParams['font.family'] = 'Verdana'
plt.style.use('ggplot')



# Apriori Algorithm and Association Rules
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules

st.header("Market Basket Analysis on Online Retail Data using Apriori Algorithm and Association Rules")

retail = pd.read_csv('Supermart_Grocery_Sales_Retail_Analytics_Dataset.csv')

# Function that filters the data frame based on city name
def choose_city(city = "all", data = retail):
    if city == "all":
        return data
    else:
        temp_df = data[data["Region"] == city]
        temp_df.reset_index(drop= True, inplace= True)
        return temp_df
    
option = st.selectbox(
    'Select Region',
    set(retail["Region"]))
city_retail = choose_city(option)
st.write(city_retail.head())

# Function that filters the data frame based on customer id
def choose_customer(customer = "all", data = city_retail):
    if customer == "all":
        return city_retail
    else:
        temp_df = city_retail[city_retail["Customer Name"] == customer]
        temp_df.reset_index(drop= True, inplace= True)
        return temp_df
    
option = st.selectbox(
    'Select Customer Name',
    set(city_retail["Customer Name"]))
customer_retail = choose_customer(option)
#st.write(customer_retail.head())
    

basket_cn = customer_retail.groupby(['Invoice', 'Sub Category']).sum()['Sales'].unstack().reset_index().fillna(0).set_index('Invoice')
# print("\nbasket_cn\n",basket_cn)

# Encode
def encoder(x):
    if(x <= 0): return 0
    if(x >= 1): return 1
    
# Apply to the dataframe
basket_cn_encoded = basket_cn.applymap(encoder)
# print("\nbasket_cn_encoded\n",basket_cn_encoded.head())


st.subheader("Filter transaction with more than 1 Items")
# We will filter out transactions that have less than 2 items 
basket_cn_encoded_filtered = basket_cn_encoded[ (basket_cn_encoded > 0).sum(axis=1) >= 2] # Columnwise sum of encoding should be >= 2
st.write(basket_cn_encoded_filtered.head())

# print("\nbasket_cn_encoded_filtered\n",basket_cn_encoded_filtered.head())

st.subheader("Apriori Algorithm")
with st.spinner('Wait for it...'):
    frequent_itemsets = apriori(basket_cn_encoded_filtered, min_support=0.20 , use_colnames=True, max_len=5)
    # print("frequent_itemsets",frequent_itemsets)
    
    # Create Association Rules
    supermarket_rules = association_rules(frequent_itemsets, metric="lift", min_threshold=0.9)
    
    # print("supermarket_rules\n",supermarket_rules)
    # print("supermarket_rules['antecedents'][0]\n",supermarket_rules['antecedents'][0], type(supermarket_rules['antecedents'][0]))
    
    # Sort values based on lift
    supermarket_rules = supermarket_rules.sort_values("lift",ascending=False).reset_index(drop= True)
    
    supermarket_rules=pd.DataFrame(supermarket_rules)
    
    # Function to convert frozenset string to set
    def convert_to_set(frozenset_str):
        return str(frozenset_str).strip("frozenset({})")    # .replace("'", "")
    
    # Apply function to the column
    supermarket_rules['antecedents'] = supermarket_rules['antecedents'].apply(convert_to_set)
    supermarket_rules['consequents'] = supermarket_rules['consequents'].apply(convert_to_set)
    # print("supermarket_rules\n",supermarket_rules)

    supermarket_rules.to_csv('Supermarket_Rules.csv', index=False)
    
    # supermarket_rules = pd.read_csv('Supermarket_Rules.csv')
    
    # supermarket_rules = supermarket_rules.sort_values("lift",ascending=False).reset_index(drop= True)



# List of all products
product_catalog = list(city_retail['Sub Category'].unique())
print(f'There are {len(product_catalog)} unique products in the marketplace.')

option2 = st.selectbox('Select Item',product_catalog)   

def remove_from_list(y, item_to_search):
    newlist = list()
    for i in y:
        if i not in item_to_search:
            newlist.append(i)
    return newlist
item_input=option2
def search_list(item_to_search, max_lift, list_to_search=supermarket_rules['antecedents']):
    item_to_recommend = []
    for i, item in enumerate(list_to_search):
        #print("INSIDE_LOOP")
        if set(item_to_search).issubset(set(item)):
            # print("INSIDE_LOOP")
            if supermarket_rules['lift'][i] > max_lift:
                # print("INSIDE_LOOP")
                max_lift = supermarket_rules['lift'][i]
                # print(f"supermarket_rules['antecedents'][{i}]\n",supermarket_rules['antecedents'][i], "\n", type(supermarket_rules['antecedents'][i]), "\n")
                # print(f"supermarket_rules['consequents'][{i}]\n",supermarket_rules['consequents'][i], "\n", type(supermarket_rules['consequents'][i]), "\n")
                antecedents = supermarket_rules['antecedents'][i]
                #antecedents.remove(item_to_search[0])
                item_to_recommend = supermarket_rules['consequents'][i] + ", " + antecedents
                # print(f"supermarket_rules['antecedents'][{i}]", supermarket_rules['antecedents'][i], f"supermarket_rules['consequents'][{i}]", supermarket_rules['consequents'][i])
    if not item_to_recommend:
        print("Oops! No product recommendations available right now!")
        item_to_search= ["Search Complete"]
    else:
        print("People who bought this also bought:", item_to_recommend)
    return item_to_search, item_to_recommend


dict_to_store = {}
for j in range (1,2):
    f = 2
    key, value = search_list(item_input, f)
    # print("\nsearch_list\n", search_list)
    # print("\nkey value\n", key[0], key, "\n", value)
    dict_to_store.update({key[0]: value})

import json

# print("dict_to_store\n",dict_to_store)
json_file = json.dumps(dict_to_store)
# open file for writing, "w" 
f = open("item_sets.json","w")
# write json object to file
f.write(json_file)

# close file
f.close()

# Opening JSON file
with open('item_sets.json') as json_file:
    data = json.load(json_file)
    
#print(data.keys())    



def display():
    numbered_list = []    
    for key in dict_to_store.keys():
        list_items = str(dict_to_store[key]).replace("'", "").split(", ")
        for i, item in enumerate(list_items):
            numbered_list.append(f"{i+1}. {item}")
            reco=("\n".join(numbered_list))
    return reco

st.subheader(f"People who bought : {option2} also bought following items :")
st.write(display())

   