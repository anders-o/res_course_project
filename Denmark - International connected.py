# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 14:24:56 2021

@author: Anders Overgaard

International connected electricity sector

- NO3 connected to DK1
- SE3 connected to DK1
- SE4 connected to DK2
- DE connected to DK1
- DE connected to DK2
- NL connected to DK1
- Possible to add CO2 constraint

- To remove a country from simulation -> comment out the section. Be 
  aware of plots.

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

# Load data: Demand and enerators for 6 regions
df_elec = pd.read_csv('data/2017_entsoe.csv', sep=',', index_col=0) # in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datatime

df_heat = pd.read_csv('data/heat_demand.csv', sep=';', index_col=0)
df_heat.index = pd.to_datetime(df_heat.index)
df_heat.index = df_heat.index + DateOffset(years=2)

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

#NO2
network.add("Carrier", "gas_no2", co2_emissions=0.19) # in t_CO2/MWh_th
network.add("Carrier", "onshorewind_no2")
network.add("Carrier", "hydro_no2")


#%% DK1

# Add busses for heat and electricity
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


#%% DK2

# Add busses for heat and electricity
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

#%% Add Norway - NO2
network.add("Bus","no2")

network.add("Load",
            "load_no2", 
            bus="no2", 
            p_set=df_elec['NO_2_load_actual_entsoe_transparency'])

no2_ons_max = max(df_elec.NO_2_wind_onshore_generation_actual)
no2_ons_CF = df_elec.NO_2_wind_onshore_generation_actual / no2_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
network.add("Generator",
            "onshorewind_no2",
            bus="no2",
            p_nom_extendable=True,
            carrier="onshorewind_no2",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = no2_ons_CF)

# Load inflow data
no2_inflow_data = pd.read_csv('data/Hydro_Inflow_NO.csv', sep=',', index_col=False) # in MWh
no2_inflow_data.index = pd.to_datetime(no2_inflow_data[['Year', 'Month', 'Day']])
no2_inflow_data.index = no2_inflow_data.index + DateOffset(years=6)
no2_inflow_data = no2_inflow_data.drop(columns=['Year','Month','Day'])
no2_inflow_data = no2_inflow_data['2017']*1000/5 #GWh to MWh, divid by 5 since 5 regions in norway



#Create a new carrier
network.add("Carrier", "no2_hydro")


#Create a new bus
network.add("Bus", "no2_hydro", carrier = "no2_hydro")
network.add("Bus", "no2_hydro_inflow", carrier = "no2_hydro")


# Hydro Inflow Generator
network.add("Generator", 
            "hydro_no2",
            bus="no2_hydro_inflow",
            carrier="hydro_no2",
            # p_nom_max = 9949, # Entsoe: installed capacity pr type MW
            p_nom_extendable = True,
            p_set = no2_inflow_data.Inflow,
            capital_cost = annuity(80,0.07)*2000000,
            marginal_cost = 0)


#Connect the store to the bus
network.add("Store",
      "no2 Hydro Reservior",
      bus = "no2_hydro",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = 0)

network.add("Link",
      "Fill reservior", 
      bus0 = "no2_hydro_inflow",
      bus1 = "no2_hydro",     
      p_nom_= 9949,
                  p_nom_extendable = True,
      efficiency = 0.87,)

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "Utilize hydro reservior", 
      bus0 = "no2_hydro",
      bus1 = "no2",     
      p_nom_extendable = True,
      efficiency = 0.87,
      capital_cost = 0)


#%% Add Sweden - SE3 
network.add("Bus","se3")

network.add("Load",
            "load_se3", 
            bus="se3", 
            p_set=df_elec['SE_3_load_actual_entsoe_transparency'])

se3_ons_max = max(df_elec.SE_3_wind_onshore_generation_actual)
se3_ons_CF = df_elec.SE_3_wind_onshore_generation_actual / se3_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
network.add("Generator",
            "onshorewind_se3",
            bus="se3",
            p_nom_extendable=True,
            carrier="onshorewind_se3",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = se3_ons_CF)

# Load inflow data
se3_inflow_data = pd.read_csv('data/Hydro_Inflow_NO.csv', sep=',', index_col=False) # in MWh
se3_inflow_data.index = pd.to_datetime(se3_inflow_data[['Year', 'Month', 'Day']])
se3_inflow_data.index = se3_inflow_data.index + DateOffset(years=6)
se3_inflow_data = se3_inflow_data.drop(columns=['Year','Month','Day'])
se3_inflow_data = se3_inflow_data['2017']*1000/4 #GWh to MWh, divid by 4 since 4 regions in sweden

#Create a new carrier
network.add("Carrier", "se3_hydro")


#Create a new bus
network.add("Bus", "se3_hydro", carrier = "se3_hydro")
network.add("Bus", "se3_hydro_inflow", carrier = "se3_hydro")


# Hydro Inflow Generator
network.add("Generator", 
            "hydro_se3",
            bus="se3_hydro_inflow",
            carrier="hydro_se3",
            # p_nom_max = 16301/4, # Entsoe: installed capacity pr type MW
            p_nom_extendable = True,
            p_set = se3_inflow_data.Inflow,
            capital_cost = annuity(80,0.07)*2000000,
            marginal_cost = 0)


#Connect the store to the bus
network.add("Store",
      "se3 Hydro Reservior",
      bus = "se3_hydro",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = 0)

network.add("Link",
      "Fill reservior se3", 
      bus0 = "se3_hydro_inflow",
      bus1 = "se3_hydro",     
      p_nom_= 16301/4,
                  p_nom_extendable = True,
      efficiency = 0.87,)

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "Utilize hydro reservior se3", 
      bus0 = "se3_hydro",
      bus1 = "se3",     
      p_nom_extendable = True,
      efficiency = 0.87,
      capital_cost = 0)

#%% Add Sweden - se4
network.add("Bus","se4")

network.add("Load",
            "load_se4", 
            bus="se4", 
            p_set=df_elec['SE_4_load_actual_entsoe_transparency'])

se4_ons_max = max(df_elec.SE_3_wind_onshore_generation_actual)
se4_ons_CF = df_elec.SE_3_wind_onshore_generation_actual / se4_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000 # in €/MW
network.add("Generator",
            "onshorewind_se4",
            bus="se4",
            p_nom_extendable=True,
            carrier="onshorewind_se4",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = se4_ons_CF)

# Load inflow data
se4_inflow_data = pd.read_csv('data/Hydro_Inflow_SE.csv', sep=',', index_col=False) # in MWh
se4_inflow_data.index = pd.to_datetime(se4_inflow_data[['Year', 'Month', 'Day']])
se4_inflow_data.index = se4_inflow_data.index + DateOffset(years=6)
se4_inflow_data = se4_inflow_data.drop(columns=['Year','Month','Day'])
se4_inflow_data = se4_inflow_data['2017']*1000/4 #GWh to MWh, divid by 4 since 4 regions in sweden

#Create a new carrier
network.add("Carrier", "se4_hydro")


#Create a new bus
network.add("Bus", "se4_hydro", carrier = "se4_hydro")
network.add("Bus", "se4_hydro_inflow", carrier = "se4_hydro")


# Hydro Inflow Generator
network.add("Generator", 
            "hydro_se4",
            bus="se4_hydro_inflow",
            carrier="hydro_se4",
            # p_nom_max = 16301/4, # Entsoe: installed capacity pr type MW
            p_nom_extendable = True,
            p_set = se4_inflow_data.Inflow,
            capital_cost = annuity(80,0.07)*2000000,
            marginal_cost = 0)


#Connect the store to the bus
network.add("Store",
      "se4 Hydro Reservior",
      bus = "se4_hydro",
      e_nom_extendable = True,
      e_cyclic = True,
      capital_cost = 0)

network.add("Link",
      "Fill reservior se4", 
      bus0 = "se4_hydro_inflow",
      bus1 = "se4_hydro",     
      p_nom_= 16301/4,
                  p_nom_extendable = True,
      efficiency = 0.87,)

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "Utilize hydro reservior se4", 
      bus0 = "se4_hydro",
      bus1 = "se4",     
      p_nom_extendable = True,
      efficiency = 0.87,
      capital_cost = 0)

#%% DE

network.add("Bus","de")

network.add("Load",
            "load_de", 
            bus="de", 
            p_set=df_elec['DE_load_actual_entsoe_transparency'])

# Add offshore wind generator
de_off_max = 4131       # Source entsoe.eu - yields max capacity factor 1.13
de_off_max = max(df_elec.DE_wind_offshore_generation_actual)
de_off_CF = df_elec.DE_wind_offshore_generation_actual / de_off_max
capital_cost_offshorewind = annuity(30,0.07)*1930000*(1+0.1) # in €/MW
network.add("Generator",
            "offshorewind_de",
            bus="de",
            p_nom_extendable=True,
            carrier="offshorewind_de",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_offshorewind,
            marginal_cost = 0,
            p_max_pu = de_off_CF)

# Add onshore wind generator
de_ons_max = 49862       # Source entsoe.eu
de_ons_CF = df_elec.DE_wind_onshore_generation_actual / de_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000*(1+0.033) # in €/MW
network.add("Generator",
            "onshorewind_de",
            bus="de",
            p_nom_extendable=True,
            carrier="onshorewind_de",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = de_ons_CF)

# Add solar PV generator
de_sol_max = 41886       # Source entsoe.eu
de_sol_CF = df_elec.DE_solar_generation_actual / de_sol_max
capital_cost_solar = annuity(25,0.07)*380000*(1+0.03) # in €/MW
network.add("Generator",
            "solar_de",
            bus="de",
            p_nom_extendable=True,
            carrier="solar_de",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = de_sol_CF)

# Add OCGT (Open Cycle Gas Turbine) generator
capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th
efficiency = 0.39
marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
network.add("Generator",
            "OCGT_de",
            bus="de",
            p_nom_extendable=True,
            carrier="gas_de",
            #p_nom_max=1000,
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

# Load inflow data
de_inflow_data = pd.read_csv('data/Hydro_Inflow_DE.csv', sep=',', index_col=False) # in MWh
de_inflow_data.index = pd.to_datetime(de_inflow_data[['Year', 'Month', 'Day']])
de_inflow_data.index = de_inflow_data.index + DateOffset(years=6)
de_inflow_data = de_inflow_data.drop(columns=['Year','Month','Day'])
de_inflow_data = de_inflow_data['2017']*1000/4 #GWh to MWh, divid by 4 since 4 regions in sweden

#Create a new carrier
network.add("Carrier", "de_hydro")


#Create a new bus
network.add("Bus", "de_hydro", carrier = "de_hydro")
network.add("Bus", "de_hydro_inflow", carrier = "de_hydro")


# Hydro Inflow Generator
network.add("Generator", 
            "hydro_de",
            bus="de_hydro_inflow",
            carrier="hydro_de",
            # p_nom_max = 9422, # Entsoe: installed capacity pr type MW
            p_nom_extendable = True,
            p_set = de_inflow_data.Inflow,
            capital_cost = annuity(80,0.07)*2000000,
            marginal_cost = 0)


#Connect the store to the bus
network.add("Store",
      "de Hydro Reservior",
      bus = "de_hydro", 
      e_cyclic = True,
      capital_cost = 0)

network.add("Link",
      "Fill reservior de", 
      bus0 = "de_hydro_inflow",
      bus1 = "de_hydro",  
            p_nom_extendable = True,      
      p_nom_max = 9422,
      efficiency = 0.87,)

#Add the link "H2 Fuel Cell" that transports energy from the H2 bus (bus0) to the electricity bus (bus1)
#with 58% efficiency
network.add("Link",
      "Utilize hydro reservior de", 
      bus0 = "de_hydro",
      bus1 = "de",     
      p_nom_extendable = True,
      efficiency = 0.87,
      capital_cost = 0)

#%% NL

network.add("Bus","nl")

network.add("Load",
            "load_nl", 
            bus="nl", 
            p_set=df_elec['NL_load_actual_entsoe_transparency'])

# Add offshore wind generator
# nl_off_max = 638       # Source entsoe.eu - yields max capacity factor 1.13
nl_off_max = max(df_elec.NL_wind_offshore_generation_actual)
nl_off_CF = df_elec.NL_wind_offshore_generation_actual / nl_off_max
capital_cost_offshorewind = annuity(30,0.07)*1930000*(1+0.1) # in €/MW
network.add("Generator",
            "offshorewind_nl",
            bus="nl",
            p_nom_extendable=True,
            carrier="offshorewind_nl",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_offshorewind,
            marginal_cost = 0,
            p_max_pu = nl_off_CF)

# Add onshore wind generator
# nl_ons_max = 3479       # Source entsoe.eu
nl_ons_max = max(df_elec.NL_wind_onshore_generation_actual)
nl_ons_CF = df_elec.NL_wind_onshore_generation_actual / nl_ons_max
capital_cost_onshorewind = annuity(30,0.07)*1040000*(1+0.033) # in €/MW
network.add("Generator",
            "onshorewind_nl",
            bus="nl",
            p_nom_extendable=True,
            carrier="onshorewind_nl",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = nl_ons_CF)

# Add solar PV generator
nl_sol_max = 2039       # Source entsoe.eu
nl_sol_CF = df_elec.NL_solar_generation_actual / nl_sol_max
capital_cost_solar = annuity(25,0.07)*380000*(1+0.03) # in €/MW
network.add("Generator",
            "solar_nl",
            bus="nl",
            p_nom_extendable=True,
            carrier="solar_nl",
            #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = nl_sol_CF)

# Add OCGT (Open Cycle Gas Turbine) generator
capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th
efficiency = 0.39
marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
network.add("Generator",
            "OCGT_nl",
            bus="nl",
            p_nom_extendable=True,
            carrier="gas_nl",
            #p_nom_max=1000,
            capital_cost = capital_cost_OCGT,
            marginal_cost = marginal_cost_OCGT)

#%% Links

# Link sizes from articles or from
# https://transparency.entsoe.eu/transmission-domain/physicalFlow/show?name=&defaultValue=false&viewType=TABLE&areaType=BORDER_BZN&atch=false&dateTime.dateTime=07.12.2021+00:00|CET|DAY&border.values=CTY|10Y1001A1001A65H!BZN_BZN|10YDK-1--------W_BZN_BZN|10Y1001A1001A46L&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)

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

# Jutland - Norway link
network.add("Link",
              'dk1 - no2',
              bus0="dk1",
              bus1="no2",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 1632, #MW - nominal power passing through link
              p_min_pu= -1,
              length=240, # length (in km) between country a and country b
              capital_cost=400*240) # capital cost * length 

# Jutland - SE3 link
network.add("Link",
              'dk1 - se3',
              bus0="dk1",
              bus1="se3",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 714, #MW - nominal power passing through link
              p_min_pu= -1,
              length=240, # length (in km) between country a and country b
              capital_cost=400*240) # capital cost * length 

# Zealand - SE4 link
network.add("Link",
              'dk2 - se4',
              bus0="dk2",
              bus1="se4",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 1734, #MW - nominal power passing through link
              p_min_pu= -1,
              length=30, # length (in km) between country a and country b
              capital_cost=400*30) # capital cost * length 

# Zealand - DE link
network.add("Link",
              'dk2 - de',
              bus0="dk2",
              bus1="de",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 600, #MW - nominal power passing through link
              p_min_pu= -1,
              length=30, # length (in km) between country a and country b
              capital_cost=400*30) # capital cost * length 


# Jutland - Germany link
network.add("Link",
              'dk1 - de',
              bus0="dk1",
              bus1="de",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 1780, #MW - nominal power passing through link
              p_min_pu= -1,
              length=200, # length (in km) between country a and country b
              capital_cost=400*200) # capital cost * length 

# Jutland - Netherlands link
network.add("Link",
              'dk1 - nl',
              bus0="dk1",
              bus1="nl",
              # p_nom_extendable=True, # capacity is optimised
              p_nom = 700, #MW - nominal power passing through link
              p_min_pu= -1,
              length=325, # length (in km) between country a and country b
              capital_cost=400*325) # capital cost * length 

#%% CO2 constraint

# co2_limit=23.6*10**6 * 0.05 #tonCO2
# network.add("GlobalConstraint",
#             "co2_limit",
#             type="primary_energy",
#             carrier_attribute="co2_emissions",
#             sense="<=",
#             constant=co2_limit)

#%% Solver

network.lopf(network.snapshots, 
              pyomo=False,
              solver_name='gurobi')

print(network.objective/network.loads_t.p.sum()) # €/MWh
print(network.generators.p_nom_opt) #in MW
network.generators_t.p_max_pu


#%% Plot
# Demand plot for contries
plt.figure()
plt.plot(df_elec.DK_1_load_actual_entsoe_transparency.resample('W').mean(),label='DK1')
plt.plot(df_elec.DK_2_load_actual_entsoe_transparency.resample('W').mean(),label='DK2')
plt.plot(df_elec.NO_2_load_actual_entsoe_transparency.resample('W').mean(),label='NO3')
plt.plot(df_elec.SE_3_load_actual_entsoe_transparency.resample('W').mean(),label='SE3')
plt.plot(df_elec.SE_4_load_actual_entsoe_transparency.resample('W').mean(),label='SE4')
plt.plot(df_elec.NL_load_actual_entsoe_transparency.resample('W').mean(),label='NL')
plt.plot(df_elec.DE_load_actual_entsoe_transparency.resample('W').mean(),label='DE')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Demand ( (,) is thousand separator) [MWh]')
plt.title('Demand for countries')
current_values = plt.gca().get_yticks()
plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values])

# Generation plot for contries
plt.figure()
plt.plot(network.generators_t.p.OCGT_nl.resample('W').mean(),label='Gas NL')
plt.plot(network.generators_t.p.solar_nl.resample('W').mean(),label='Solar NL')
plt.plot(network.generators_t.p.offshorewind_nl.resample('W').mean(),label='Offshore NL')
plt.plot(network.generators_t.p.hydro_de.resample('W').mean(),label='Hydro DE')
plt.plot(network.generators_t.p.OCGT_de.resample('W').mean(),label='Gas DE')
plt.plot(network.generators_t.p.solar_de.resample('W').mean(),label='Solar DE')
plt.plot(network.generators_t.p.offshorewind_de.resample('W').mean(),label='Offshore DE')
plt.plot(network.generators_t.p.hydro_se4.resample('W').mean(),label='Hydro SE4')
plt.plot(network.generators_t.p.hydro_se3.resample('W').mean(),label='Hydro SE3')
plt.plot(network.generators_t.p.hydro_no2.resample('W').mean(),label='Hydro NO2')
plt.plot(network.generators_t.p.OCGT_dk2.resample('W').mean(),label='Gas DK2')
plt.plot(network.generators_t.p.solar_dk2.resample('W').mean(),label='Solar DK2')
plt.plot(network.generators_t.p.onshorewind_dk2.resample('W').mean(),label='Onshore DK2')
plt.plot(network.generators_t.p.OCGT_dk1.resample('W').mean(),label='Gas DK1')
plt.plot(network.generators_t.p.solar_dk1.resample('W').mean(),label='Solar DK1')
plt.plot(network.generators_t.p.onshorewind_dk1.resample('W').mean(),label='Onshore DK1')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Generation [MW]')
plt.title('Generation per type')

# Plots for debugging
# Generator and load overview
# network.generators_t.p.div(1e3).plot.area(subplots=True, ylabel='GW')
# network.loads_t.p.div(1e3).plot.area(subplots=True, ylabel='GW')

