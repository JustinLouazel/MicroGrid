
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#																										SERIOUS GAME MICROGRID : SOLAR FARM
#Authors :  Mehdi-Lou Pigeard & Justin Louazel
# Date : 16/05/2021
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
import pulp

from bokeh.layouts import row
from bokeh.plotting import figure, show


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

		self.pd = 0.95 # discharge efficiency
		self.pc = 0.95 # charge efficiency
		self.C = 30#kWh -- capacity of the battery



	def set_scenario(self, scenario_data):
		data_selected = scenario_data[scenario_data["region"]==self.region_name][scenario_data[scenario_data["region"]==self.region_name]["day"]==self.day] # on selectionne les données sur la région et le jour considéré.
		self.data = np.zeros(self.horizon)
		for i in range(0, 24): # on remplit deux cases à chaque fois avec la même production car les données sont données par heures
			self.data[2*i]=data_selected["pv_prod (W/m2)"][i]
			self.data[2*i+1]=data_selected["pv_prod (W/m2)"][i]



	def set_prices(self, prices):
		self.prices = prices

	def compute_all_load(self):

		lp = pulp.LpProblem("lp", pulp.LpMinimize)
		lp.setSolver()
		l_bat = {}

		l_bat_plus = {}
		l_bat_moins = {}

		for t in range(self.horizon):
			var_name = "l_bat n°"+str(t)
			l_bat[t] = pulp.LpVariable(var_name,-self.pMax,self.pMax) # la mise dans la batterie est limitée par pMax
			constraint_name = "power_limit_l_bat n°"+str(t)
			lp += l_bat[t]-self.data[t]<=self.pMax,constraint_name

			var_name = "l_bat_plus n°"+str(t)
			l_bat_plus[t] = pulp.LpVariable(var_name,0, None)
			constraint_name = "upper_bound_l_bat_plus" + str(t)
			lp+= l_bat[t]<=l_bat_plus[t],constraint_name

			var_name = "l_bat_moins n°"+str(t)
			l_bat_moins[t] = pulp.LpVariable(var_name,0, None)
			constraint_name = "upper_bound_l_bat_moins" + str(t)
			lp+= -l_bat[t]<=l_bat_moins[t],constraint_name

			constraint_name = "equality of battery exchanges"+str(t)
			lp+= l_bat[t] == l_bat_plus[t]-l_bat_moins[t],constraint_name

			constraint_name = "lower_bound_stock_"+str(t)
			lp += self.pc*pulp.lpSum([l_bat_plus[i] for i in range(t)])-1/self.pd*pulp.lpSum([l_bat_moins[i] for i in range(t)]) >= 0,constraint_name
			constraint_name = "upper_bound_stock_"+str(t)
			lp += (self.pc*pulp.lpSum([l_bat_plus[i] for i in range(t)])-1/self.pd*pulp.lpSum([l_bat_moins[i] for i in range(t)])) <= self.C/self.time_interval,constraint_name

			constraint_name = "dispo_batterie" + str(t)
			lp+= l_bat[t]<=self.data[t], constraint_name # l'intant initial, la batterie est vide, on peut simplement remplir ce qui vient d'être produit



		constraint_name = "empty the battery"
		lp += (self.pc*pulp.lpSum([l_bat_plus[i] for i in range(self.horizon)])-1/self.pd*pulp.lpSum([l_bat_moins[i] for i in range(self.horizon)]))*self.time_interval == 0,constraint_name



		lp.setObjective(pulp.lpSum([self.prices[t]*(l_bat[t]-self.data[t]) for t in range(self.horizon)]))
		lp.solve()

		affLbat = np.zeros(self.horizon)
		affBatt = np.zeros(self.horizon)
		for t in range(self.horizon):
			affLbat[t]=l_bat[t].varValue
			if t!= 0 :
				affBatt[t]=affBatt[t-1]+(self.pc*l_bat_plus[t].varValue-1/self.pd*l_bat_moins[t].varValue)*self.time_interval


##Affichage des résultats
		p_prix = figure(title="Prix par jour", x_axis_label="t", y_axis_label="prix")
		p_prix.vbar(x=range(self.horizon),top=self.prices)


		p_prod = figure(title="Productions par jour",x_axis_label="pas de temps t",y_axis_label="Production en kW")
		p_prod.line(range(self.horizon),affLbat,legend_label="l_bat",line_color = "blue")
		p_prod.line(range(self.horizon),self.data,legend_label="Production solaire",line_color = "red")
		p_prod.line(range(self.horizon),affLbat-self.data,legend_label="Production vendue",line_color = "yellow")


		p_batt = figure(title="Remplissage de la batterie par jour",x_axis_label="pas de temps t",y_axis_label="Énergie stockée (kWh)")
		p_batt.vbar(x=range(self.horizon),top=affBatt,width=1)


		show(row(p_prix,p_prod,p_batt))


		return pulp.value(lp.objective)

	def take_decision(self, time):







		# stock_remaining = self.battery.getCapacity()-self.battery.getBattery(time-1)
		#
		# if time == self.horizon-1 : # au dernier pas de temps, on vend tout le stock
		# 	self.l_bat[time] = -self.battery.getBattery(time-1)
		# elif self.prices[time]<self.prices[time+1] : # si le prix le prix le lendemain est plus intéressant, on stocke au maximum
		# 	if self.data[time] < stock_remaining :
		# 		self.l_bat[time] = self.data[time]
		# 	else :
		# 		self.l_bat[time] = stock_remaining
		# else :
		# 	if self.battery.getBattery(time-1)+self.data[time] < self.pMax : # si on ne dépasse pas la puissance maximale sur la ligne
		# 		self.l_bat[time] = -self.battery.getBattery(time-1)
		# 	else :
		# 		self.l_bat[time]  = self.data[time] - self.pMax
		# self.battery.updateStock(time,self.l_bat[time])
		# print(self.battery.getBattery(time))
		# return self.l_bat[time]-self.data[time] # on retourne l3(t)

		return 0


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


player = Player()
player.set_scenario(data_csv)
player.set_prices(np.random.rand(48))
print(player.compute_all_load())
































