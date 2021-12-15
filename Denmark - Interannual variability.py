# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 14:24:56 2021

@author: Anders Overgaard

Script created for determination of optimal power generation mix looking at 
interannual power production variability of DK1 and DK2. 

- Plots the generation mix as function of time 
- Plots the average optimal capacity with standard deviation as function of 
technology

Reads data for the period 2015-2019 dowloaded from 
data.open-power-system-data.org

Capacity factor is determined using installed capacity per production type 
data from www.transparency.entsoe.eu

"""

#%% Import and define
import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates


def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n

# Create network and snapshot
network = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01T00:00Z','2015-12-31T23:00Z', freq='H')
hours_in_2016 = pd.date_range('2016-01-01T00:00Z','2016-12-31T23:00Z', freq='H')
hours_in_2017 = pd.date_range('2017-01-01T00:00Z','2017-12-31T23:00Z', freq='H')
hours_in_2018 = pd.date_range('2018-01-01T00:00Z','2018-12-31T23:00Z', freq='H')
hours_in_2019 = pd.date_range('2019-01-01T00:00Z','2019-12-31T23:00Z', freq='H')

dk1_off_max = [843,843,843,1277,1277]
dk1_ons_max = [2966,2966,2966,3664,3669]
dk1_sol_max = [421,421,421,664,672]
dk2_off_max = [428,428,428,423,423]
dk2_ons_max = [608,608,608,759,757]
dk2_sol_max = [180,180,180,338,342]

hours_in = [hours_in_2015,hours_in_2016,hours_in_2017,hours_in_2018,hours_in_2019]
years = [2015, 2016, 2017, 2018, 2019]



# Load data: Demand and generators for 6 regions
df_elec = pd.read_csv('data/data/annual_renewable_generation_dk1_dk2.csv', sep=',', index_col=0) # in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datatime

#%% Constants

network.add("Carrier", "gas_dk1", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "gas_dk2", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_dk1")
network.add("Carrier", "offshorewind_dk1")
network.add("Carrier", "solar_dk1")
network.add("Carrier", "onshorewind_dk2")
network.add("Carrier", "offshorewind_dk2")
network.add("Carrier", "solar_dk2")

network.add("Bus","dk1")
network.add("Bus","dk2")

# DK1 Add OCGT (Open Cycle Gas Turbine) generator
capital_cost_OCGT = annuity(25,0.07)*560000 # in €/MW
fuel_cost = 21.6 # in €/MWh_th
efficiency = 0.41
marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
network.add("Generator",
            "OCGT_dk1",
            bus="dk1",
            p_nom_extendable=True,
            carrier="gas_dk1",
            #p_nom_max=1000,
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

# DK2 Add OCGT (Open Cycle Gas Turbine) generator
capital_cost_OCGT = annuity(25,0.07)*560000 # in €/MW
fuel_cost = 21.6 # in €/MWh_th
efficiency = 0.41
marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
network.add("Generator",
            "OCGT_dk2",
            bus="dk2",
            p_nom_extendable=True,
            carrier="gas_dk2",
            #p_nom_max=1000,
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

# Great Belt link
network.add("Link",
              'dk1 - dk2',
              bus0="dk1",
              bus1="dk2",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 600, #MW - nominal power passing through link
              p_min_pu= -1,
              length=58, # length (in km) between country a and country b
              capital_cost=400*58) # capital cost * length 

#%% Variables

# Create lists for results
onshoredk = []
offshoredk = []
solardk = []
ocgtdk = []

cfsolar1 = []
cfonshore1 = []
cfoffshore1 = []
cfsolar2 = []
cfonshore2 = []
cfoffshore2 = []

for idx, val in enumerate(years):
    
    network.set_snapshots(hours_in[idx])
       
    network.add("Load",
            "load_dk1", 
            bus="dk1", 
            p_set=df_elec.DK_1_load_actual_entsoe_transparency[hours_in[idx]])

    network.add("Load",
            "load_dk2", 
            bus="dk2", 
            p_set=df_elec.DK_2_load_actual_entsoe_transparency[hours_in[idx]])
    

    
    # Add generators
    dk1_off_CF = df_elec.DK_1_wind_offshore_generation_actual[hours_in[idx]]/ dk1_off_max[idx]
    capital_cost_offshorewind = annuity(30,0.07)*1930000 # in €/MW
    network.add("Generator",
                "offshorewind_dk1",
                bus="dk1",
                p_nom_extendable=True,
                carrier="offshorewind_dk1",
                capital_cost = capital_cost_offshorewind,
                marginal_cost = 0,
                p_max_pu = dk1_off_CF)
    
    dk1_ons_CF = df_elec.DK_1_wind_onshore_generation_actual[hours_in[idx]] / dk1_ons_max[idx]
    capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
    network.add("Generator",
                "onshorewind_dk1",
                bus="dk1",
                p_nom_extendable=True,
                carrier="onshorewind_dk1",
                capital_cost = capital_cost_onshorewind,
                marginal_cost = 0,
                p_max_pu = dk1_ons_CF)
    
    dk1_sol_CF = df_elec.DK_1_solar_generation_actual[hours_in[idx]] / dk1_sol_max[idx]
    capital_cost_solar = annuity(40,0.07)*380000 # in €/MW
    network.add("Generator",
                "solar_dk1",
                bus="dk1",
                p_nom_extendable=True,
                carrier="solar_dk1",
                capital_cost = capital_cost_solar,
                marginal_cost = 0,
                p_max_pu = dk1_sol_CF)
    
    dk2_off_CF = df_elec.DK_2_wind_offshore_generation_actual[hours_in[idx]] / dk2_off_max[idx]
    capital_cost_offshorewind = annuity(30,0.07)*1930000 # in €/MW
    network.add("Generator",
                "offshorewind_dk2",
                bus="dk2",
                p_nom_extendable=True,
                carrier="offshorewind_dk2",
                capital_cost = capital_cost_offshorewind,
                marginal_cost = 0,
                p_max_pu = dk2_off_CF)
    
    dk2_ons_CF = df_elec.DK_2_wind_onshore_generation_actual[hours_in[idx]] / dk2_ons_max[idx]
    capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
    network.add("Generator",
                "onshorewind_dk2",
                bus="dk2",
                p_nom_extendable=True,
                carrier="onshorewind_dk2",
                capital_cost = capital_cost_onshorewind,
                marginal_cost = 0,
                p_max_pu = dk2_ons_CF)
    
    dk2_sol_CF = df_elec.DK_2_solar_generation_actual[hours_in[idx]] / dk2_sol_max[idx]
    capital_cost_solar = annuity(40,0.07)*380000 # in €/MW
    network.add("Generator",
                "solar_dk2",
                bus="dk2",
                p_nom_extendable=True,
                carrier="solar_dk2",
                capital_cost = capital_cost_solar,
                marginal_cost = 0,
                p_max_pu = dk2_sol_CF)

    # Solve
    network.lopf(network.snapshots, 
              pyomo=False,
              solver_name='gurobi')
    
    # Store data
    onshoredk.append(network.generators.p_nom_opt.onshorewind_dk1+network.generators.p_nom_opt.onshorewind_dk2)
    offshoredk.append(network.generators.p_nom_opt.offshorewind_dk1+network.generators.p_nom_opt.offshorewind_dk2)
    solardk.append(network.generators.p_nom_opt.solar_dk1+network.generators.p_nom_opt.solar_dk2)
    ocgtdk.append(network.generators.p_nom_opt .OCGT_dk1+network.generators.p_nom_opt.OCGT_dk2)
    cfsolar1.append(np.mean(dk1_sol_CF))
    cfsolar2.append(np.mean(dk2_sol_CF))
    cfonshore1.append(np.mean(dk1_ons_CF))
    cfonshore2.append(np.mean(dk2_ons_CF))
    cfoffshore1.append(np.mean(dk1_off_CF))
    cfoffshore2.append(np.mean(dk2_off_CF))
    
    # Remove generators so they can be replaced in loop
    network.remove("Generator","offshorewind_dk1")
    network.remove("Generator","onshorewind_dk1")
    network.remove("Generator","solar_dk1")
    network.remove("Generator","offshorewind_dk2")
    network.remove("Generator","onshorewind_dk2")
    network.remove("Generator","solar_dk2")
    network.remove("Load","load_dk1")
    network.remove("Load","load_dk2")
    
avgonshore = np.mean(onshoredk)
avgoffshore = np.mean(offshoredk)
avgsolar = np.mean(solardk)
avggas = np.mean(ocgtdk)

x = ['Onshore Wind','Offshore Wind','Solar','Gas (OCGT)']
yval = [avgonshore, avgoffshore, avgsolar, avggas]
yerr = [np.std(onshoredk), np.std(offshoredk), np.std(solardk), np.std(ocgtdk), ]

plt.figure()
plt.errorbar(x,yval,yerr=yerr,fmt='o')
plt.xlabel('Technology')
plt.ylabel('Average Optimal Capacity [MW]')
plt.title('Average Optimal Capacity and Standard Deviation for Different\n Technologies in Denmark in the Period 2015-2019')

plt.figure()
plt.plot(years,onshoredk,label='Onshore',color='blue')
plt.plot(years,offshoredk,label='Offshore',color='royalblue')
plt.plot(years,solardk,label='Solar',color='orange')
plt.plot(years,ocgtdk, label='Gas (OCGT)',color='brown')
plt.legend(fancybox=True, shadow=True, loc='best')
plt.title('Generation Mix as Function of Time')
plt.xlabel('CO2 reduction [%]')
plt.ylabel('Installed Capacity [MW]')
plt.xticks(np.arange(min(years), max(years)+1, 1.0))

#Average Capacity Factors
plt.figure()
plt.plot(years,cfoffshore1,label='Offshore DK1')
plt.plot(years,cfoffshore2, label='Offshore DK2')
plt.plot(years,cfonshore1,label='Onshore DK1')
plt.plot(years,cfonshore2,label='Onshore DK2')
plt.plot(years,cfsolar1, label='Solar DK1')
plt.plot(years,cfsolar2, label='Solar DK2')
plt.title('Average Capacity Factors')
plt.xlabel('Year')
plt.ylabel('Capacity Factor')
plt.xticks(np.arange(min(years), max(years)+1, 1.0))
plt.legend(fancybox=True, shadow=True, loc='best')



