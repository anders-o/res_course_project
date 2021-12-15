# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 14:24:56 2021

@author: Anders Overgaard

Basic script created for determination of optimal power generation mix looking at 
interannual power production variability of DK1 and DK2. 

- Possibility to add CO2-constraint
- Hydrogen storage added

Reads data for the period 2017 dowloaded from 
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
hours_in_2017 = pd.date_range('2017-01-01T00:00Z','2017-12-31T23:00Z', freq='H')
network.set_snapshots(hours_in_2017)

# Load data: Demand and generators for 6 regions
df_elec = pd.read_csv('data/2017_entsoe.csv', sep=',', index_col=0) # in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datatime

#%% Carriers

#DK1
network.add("Carrier", "gas_dk1", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_dk1")
network.add("Carrier", "offshorewind_dk1")
network.add("Carrier", "solar_dk1")

#DK2
network.add("Carrier", "gas_dk2", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_dk2")
network.add("Carrier", "offshorewind_dk2")
network.add("Carrier", "solar_dk2")


#%% DK1

network.add("Bus","dk1")

network.add("Load",
            "load_dk1", 
            bus="dk1", 
            p_set=df_elec['DK_1_load_actual_entsoe_transparency'])

# Add offshore wind generator
dk1_off_max = 843       # Source entsoe.eu
dk1_off_CF = df_elec.DK_1_wind_offshore_generation_actual / dk1_off_max
capital_cost_offshorewind = annuity(30,0.07)*1930000 # in €/MW
network.add("Generator",
            "offshorewind_dk1",
            bus="dk1",
            p_nom_extendable=True,
            carrier="offshorewind_dk1",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_offshorewind,
            marginal_cost = 0,
            p_max_pu = dk1_off_CF)

# Add onshore wind generator
dk1_ons_max = 2966       # Source entsoe.eu
dk1_ons_CF = df_elec.DK_1_wind_onshore_generation_actual / dk1_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
network.add("Generator",
            "onshorewind_dk1",
            bus="dk1",
            p_nom_extendable=True,
            carrier="onshorewind_dk1",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = dk1_ons_CF)

# Add solar PV generator
dk1_sol_max = 421       # Source entsoe.eu
dk1_sol_CF = df_elec.DK_1_solar_generation_actual / dk1_sol_max
capital_cost_solar = annuity(40,0.07)*380000 # in €/MW
network.add("Generator",
            "solar_dk1",
            bus="dk1",
            p_nom_extendable=True,
            carrier="solar_dk1",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = dk1_sol_CF)

# Add OCGT (Open Cycle Gas Turbine) generator
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

# Add storage
# Create a new carrier
network.add("Carrier",
      "H2_dk1")

#Create a new bus
network.add("Bus",
      "H2",
      carrier = "H2_dk1")

#Connect the store to the bus
network.add("Store",
      "H2 Tank",
      bus = "H2",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(25, 0.07)*57000*(1+0.011))

#Add the lysis" that transport energy from the electricity bus (bus0) to the H2 bus (bus1)
#with 80% efficiency
network.add("Link",
      "H2 Electrolysis", 
      bus0 = "dk1",
      bus1 = "H2",     
      p_nom_extendable = True,
      efficiency = 0.8,
      capital_cost = annuity(25, 0.07)*600000*(1+0.05))

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "H2 Fuel Cell", 
      bus0 = "H2",
      bus1 = "dk1",     
      p_nom_extendable = True,
      efficiency = 0.58,
      capital_cost = annuity(10, 0.07)*1300000*(1+0.05)) 


#%% DK2

network.add("Bus","dk2")

network.add("Load",
            "load_dk2", 
            bus="dk2", 
            p_set=df_elec['DK_2_load_actual_entsoe_transparency'])

# Add offshore wind generator
dk2_off_max = 428       # Source entsoe.eu
dk2_off_CF = df_elec.DK_2_wind_offshore_generation_actual / dk2_off_max
capital_cost_offshorewind = annuity(30,0.07)*1930000 # in €/MW
network.add("Generator",
            "offshorewind_dk2",
            bus="dk2",
            p_nom_extendable=True,
            carrier="offshorewind_dk2",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_offshorewind,
            marginal_cost = 0,
            p_max_pu = dk2_off_CF)

# Add onshore wind generator
dk2_ons_max = 608       # Source entsoe.eu
dk2_ons_CF = df_elec.DK_2_wind_onshore_generation_actual / dk2_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
network.add("Generator",
            "onshorewind_dk2",
            bus="dk2",
            p_nom_extendable=True,
            carrier="onshorewind_dk2",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = dk2_ons_CF)

# Add solar PV generator
dk2_sol_max = 180       # Source entsoe.eu
dk2_sol_CF = df_elec.DK_2_solar_generation_actual / dk2_sol_max
capital_cost_solar = annuity(40,0.07)*380000 # in €/MW
network.add("Generator",
            "solar_dk2",
            bus="dk2",
            p_nom_extendable=True,
            carrier="solar_dk2",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = dk2_sol_CF)

# Add OCGT (Open Cycle Gas Turbine) generator
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

# Add storage
# Create a new carrier
network.add("Carrier",
      "H2_dk2")

#Create a new bus
network.add("Bus",
      "H2_bus_dk2",
      carrier = "H2_dk2")

#Connect the store to the bus
network.add("Store",
      "H2 Tank DK2",
      bus = "H2_bus_dk2",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(25, 0.07)*57000*(1+0.011))

#Add the link "H2 Electrolysis" that transport energy from the electricity bus (bus0) to the H2 bus (bus1)
#with 80% efficiency
network.add("Link",
      "H2 Electrolysis dk2", 
      bus0 = "dk1",
      bus1 = "H2_bus_dk2",     
      p_nom_extendable = True,
      efficiency = 0.8,
      capital_cost = annuity(25, 0.07)*600000*(1+0.05))

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "H2 Fuel Cell dk2", 
      bus0 = "H2_bus_dk2",
      bus1 = "dk1",     
      p_nom_extendable = True,
      efficiency = 0.58,
      capital_cost = annuity(10, 0.07)*1300000*(1+0.05))

#%% Links

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


co2_limit=23.6*10**6 * 0.025 #tonCO2
network.add("GlobalConstraint",
            "co2_limit",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=co2_limit)

#%% Solver

network.lopf(network.snapshots, 
              pyomo=False,
              solver_name='gurobi')


#print(network.objective/1000000) #in 10^6 €
print(network.objective/network.loads_t.p.sum()) # €/MWh
network.generators.p_nom_opt #in MW
network.generators_t.p_max_pu

#%% Plots
# First week of January
plt.figure()
plt.plot(network.stores_t.e['H2 Tank'],color='green',label='H2') #H2
plt.plot(df_elec.DK_1_load_actual_entsoe_transparency + df_elec.DK_2_load_actual_entsoe_transparency,color='black',label='Demand')
plt.plot(network.generators_t.p['offshorewind_dk1'],color='royalblue',label='Offshore')
plt.plot(network.generators_t.p['onshorewind_dk1'],color='blue',label='Onshore')
plt.plot(network.generators_t.p['solar_dk1'],color='orange',label='Solar') 
plt.plot(network.generators_t.p['OCGT_dk1'],color='brown',label='Gas')
plt.xlim(['2017-01-01'],['2017-01-07'])
plt.xlabel('Date')
plt.ylabel('Generation [MW]')
plt.legend()

# First week of july
plt.figure()
plt.plot(network.stores_t.e['H2 Tank'],color='green',label='H2') #H2
plt.plot(df_elec.DK_1_load_actual_entsoe_transparency + df_elec.DK_2_load_actual_entsoe_transparency,color='black',label='Demand')
plt.plot(network.generators_t.p['offshorewind_dk1'],color='royalblue',label='Offshore')
plt.plot(network.generators_t.p['onshorewind_dk1'],color='blue',label='Onshore')
plt.plot(network.generators_t.p['solar_dk1'],color='orange',label='Solar') 
plt.plot(network.generators_t.p['OCGT_dk1'],color='brown',label='Gas')
plt.xlim(['2017-07-01'],['2017-07-07'])
plt.xlabel('Date')
plt.ylabel('Generation [MW]')
plt.legend()

# Capacity factor offshore wind DK1
plt.figure()
plt.plot(dk1_off_CF.resample('D').mean(), color='lightskyblue', label='Daily average')
plt.plot(dk1_off_CF.resample('M').mean(), color='darkorange',label='Monthly average')
plt.plot(dk1_off_CF.resample('W').mean(), color='brown',label='Weekly average')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Capacity factor')
plt.title('Capacity Factor of Offshore Wind DK1')

# Capacity factor offshore wind DK2
plt.figure()
plt.plot(dk2_off_CF.resample('D').mean(), color='lightskyblue', label='Daily average')
plt.plot(dk2_off_CF.resample('M').mean(), color='darkorange',label='Monthly average')
plt.plot(dk2_off_CF.resample('W').mean(), color='brown',label='Weekly average')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Capacity factor')
plt.title('Capacity Factor of Offshore Wind DK2')

dk1_off_CF.max()
dk2_off_CF.max()
# network.generators_t.p.div(1e3).plot.area(subplots=True, ylabel='GW')