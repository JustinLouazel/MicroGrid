
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#																										SERIOUS GAME MICROGRID : SOLAR FARM
#Authors :  Mehdi-Lou Pigeard & Justin Louazel
# Date : 16/05/2021
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd

data_csv=pd.read_csv("/home/justin/Documents/Cours/Optimisation_et_energie/seriousGame/microgrid-player/data/pv_prod_scenarios.csv",delimiter=";")

TIME_HORIZON=48

## Main class containinf functions that calculate the strategy
class Player:

	def __init__(self,region = "grand_nord",day="01/01/2014"):
		# some player might not have parameters
		self.parameters = 0
		self.horizon = TIME_HORIZON

		# global parameters
		self.time_interval = 24/self.horizon

		# data parameters
		#NB : we assume that the user knows the correct format for the dates and the region
		self.region_name = region
		self.day = day
		self.l_bat = np.zeros(self.horizon)
		self.battery = Battery(self.horizon)
		self.pMax = 10#kWh

	def set_scenario(self, scenario_data):
		data_selected = scenario_data[scenario_data["region"]==self.region_name][scenario_data[scenario_data["region"]==self.region_name]["day"]==self.day] # on selectionne les données sur la région et le jour considéré.
		self.data = np.zeros(self.horizon)
		for i in range(0, 24): # on remplit deux cases à chaque fois avec la même production car les données sont données par heures
			print(i)
			self.data[2*i]=data_selected["pv_prod (W/m2)"][i]
			self.data[2*i+1]=data_selected["pv_prod (W/m2)"][i]



	def set_prices(self, prices):
		self.prices = prices

	def compute_all_load(self):
		load = np.zeros(self.horizon)
		for time in range(self.horizon):
			load[time] = self.compute_load(time)
			print(self.battery.getBattery(time))

		return load

	def take_decision(self, time):

		stock_remaining = self.battery.getCapacity()-self.battery.getBattery(time-1)

		if time == self.horizon-1 : # au dernier pas de temps, on vend tout le stock
			self.l_bat[time] = -self.battery.getBattery(time-1)
		elif self.prices[time]<self.prices[time+1] : # si le prix le prix le lendemain est plus intéressant, on stocke au maximum
			if self.data[time] < stock_remaining :
				self.l_bat[time] = self.data[time]
			else :
				self.l_bat[time] = stock_remaining
		else :
			if self.battery.getBattery(time-1)+self.data[time] < self.pMax : # si on ne dépasse pas la puissance maximale sur la ligne
				self.l_bat[time] = -self.battery.getBattery(time-1)
			else :
				self.l_bat[time]  = self.data[time] - self.pMax
		self.battery.updateStock(time,self.l_bat[time])
		return self.l_bat[time]-self.data[time] # on retourne l3(t)

	def compute_load(self, time):
		load = self.take_decision(time)
		return load

	def reset(self):
		# reset all observed data
		pass

## Class modeling the battery, so that it is used by the class Player.
class Battery :

	def __init__(self,size):

		self.pd = 0.95 # discharge efficiency
		self.pc = 0.95 # charge efficiency
		self.C = 30#kWh -- capacity of the battery
		self.pMax = 10 #kWh max (dis)charge of the battery

		self.availability = np.zeros(size)


		self.horizon = TIME_HORIZON
		self.time_interval = 24/self.horizon


	def getBattery(self,time):
		return self.availability[time]

	def updateStock(self,time,add):
		if add > 0 :
			self.availability[time] = self.availability[time-1]+self.pc*add*self.time_interval
		else :
			self.availability[time] = self.availability[time-1]+1/self.pd*add*self.time_interval
		return 0

	def getCapacity(self):
		return self.C
	def getpMax(self):
		return self.pMax



































