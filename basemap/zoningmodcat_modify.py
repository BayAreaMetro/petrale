#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd


# In[5]:


pcl19 = pd.read_csv('07_11_2019_parcels_geography.csv')
p10_pba50_att = pd.read_csv('p10_pba50_attr_20200221.csv')


# In[6]:


pcl19.head()


# In[8]:


p10_pba50_att.head()


# In[16]:


# check unique ID in both tables
print(len(pcl19.geom_id.unique()) == pcl19.shape[0])
print(len(p10_pba50_att.GEOM_ID.unique()) == p10_pba50_att.shape[0])

print(pcl19.shape[0])
print(p10_pba50_att.shape[0])


# In[31]:


pcl19['geom_id'] = pcl19['geom_id'].apply(lambda x: int(x))
p10_pba50_att['geom_id_s'] = p10_pba50_att['geom_id_s'].apply(lambda x: int(x))
merg_outer = pd.merge(pcl19,p10_pba50_att, how='outer', left_on='geom_id', right_on='geom_id_s')
display(merg_outer.head())
merg_outer.shape[0]


# In[36]:


missing50cat = merg_outer.loc[merg_outer.pba50zoningmodcat.isnull()]
display(missing50cat)
print(missing50cat.shape[0] / pcl19.shape[0])


# In[53]:


pcl_new = pd.merge(pcl19, p10_pba50_att[['geom_id_s','pba50zoningmodcat']],how='outer', left_on='geom_id', right_on='geom_id_s')
pcl_new.drop(columns=['geom_id_s'],inplace = True)
display(pcl_new)
pcl_new.to_csv('02_21_2020_parcels_geography.csv', index = False)

