# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 14:24:56 2021

@author: Anders Overgaard

Script created for determination of optimal power generation mix with 
power production from DK1 and DK2. 

- Includes heating sector
- Possible to add CO2 constraint

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
from pandas.tseries.offsets import DateOffset

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

df_heat = pd.read_csv('data/heat_demand.csv', sep=';', index_col=0)
df_heat.index = pd.to_datetime(df_heat.index)
df_heat.index = df_heat.index + DateOffset(years=2)

# Assume 2/3 of heat is used in DK1 and 1/3 of heat in DK2
df_heat_dk1 = df_heat * 2/3
df_heat_dk2 = df_heat * 1/3

#%% Carriers

#DK1
network.add("Carrier", "gas_dk1", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_dk1")
network.add("Carrier", "offshorewind_dk1")
network.add("Carrier", "solar_dk1")
network.add("Carrier", "heat")

#DK2
network.add("Carrier", "gas_dk2", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_dk2")
network.add("Carrier", "offshorewind_dk2")
network.add("Carrier", "solar_dk2")


#%% DK1

# Add busses for heat and electricity
network.add("Bus","dk1")
network.add("Bus","dk1 heat", carrier="heat")
network.add("Load",
            "load_dk1", 
            bus="dk1", 
            p_set=df_elec['DK_1_load_actual_entsoe_transparency'])

network.add("Load",
            "Load_heat_dk",
            bus="dk1",
            p_set=df_heat_dk1['DNK'])

# Add heat pump
capital_cost_heatpump = annuity(25,0.07)*1300000 #€/MJ
network.add("Link",
            "Heat pump",
            bus0 = "dk1",
            bus1 = "dk1 heat",
            efficiency = 3,
            capital_cost = capital_cost_heatpump,
            p_nom_extendable=True)


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

#Connect the store to the bus6
network.add("Store",
      "H2 Tank",
      bus = "H2",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = annuity(25, 0.07)*57000*(1+0.011))

#Add the link "H2 Electrolysis" that transport energy from the electricity bus (bus0) to the H2 bus (bus1)
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

# Add busses for heat and electricity
network.add("Bus","dk2")
network.add("Bus","dk2 heat", carrier="heat 2")
network.add("Load",
            "Load_heat_dk2",
            bus="dk2",
            p_set=df_heat_dk2['DNK'])

network.add("Link",
            "Heat pump 2",
            bus0 = "dk2",
            bus1 = "dk2 heat",
            efficiency = 3,
            capital_cost = capital_cost_heatpump,
            p_nom_extendable=True)

# Add heat pump
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

# Add hydrogen storage
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


#%% CO2 constraint

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

print(network.objective/network.loads_t.p.sum()) # €/MWh
print(network.generators.p_nom_opt) #in MW
network.generators_t.p_max_pu

# Total load
tot_elec_load = network.loads_t.p.load_dk1.sum()+network.loads_t.p.load_dk2.sum()
tot_heat_load = network.loads_t.p.Load_heat_dk.sum()+network.loads_t.p.Load_heat_dk2.sum()

#%% Plot

# Average demand of electricity and heat
plt.figure()
plt.plot(network.loads_t.p.load_dk1.resample('W').mean(),color='palegreen',label='Electricirty DK1')
plt.plot(network.loads_t.p.Load_heat_dk.resample('W').mean(),color='chocolate',label='Heat DK1')
plt.plot(network.loads_t.p.load_dk2.resample('W').mean(),color='yellowgreen',label='Electricity DK2')
plt.plot(network.loads_t.p.Load_heat_dk2.resample('W').mean(),color='sandybrown',label='Heat DK2')
plt.xlabel('Time')
plt.ylabel('Load [MW]')
plt.title('Weekly average electricity and heat demand for 2017')
plt.legend()


# Plots for debugging
# Generator and load overview
# network.generators_t.p.div(1e3).plot.area(subplots=True, ylabel='GW')
# network.loads_t.p.div(1e3).plot.area(subplots=True, ylabel='GW')