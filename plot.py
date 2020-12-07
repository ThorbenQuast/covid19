import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
from matplotlib.pyplot import figure
figure(num=None, figsize=(12, 9), dpi=80, facecolor='w', edgecolor='k')

import os, re, datetime

data_path_infected = os.path.abspath("data/time_series_covid19_confirmed_global.csv")
data_path_deaths = os.path.abspath("data/time_series_covid19_deaths_global.csv")
data_path_recovered = os.path.abspath("data/time_series_covid19_recovered_global.csv")
restriction_dates = {
	"Switzerland": datetime.date(2020, 1, 30),
	"Italy": datetime.date(2020, 3, 12),
	"France": datetime.date(2020, 3, 17),
	"Germany": datetime.date(2020, 3, 22),
	"UK": datetime.date(2020, 3, 24),
}
population = {
	"Switzerland": 8.6e6,
	"Italy": 60.3e6,
	"France": 67.1e6,
	"Germany": 83e6,
	"UK": 66.7e6,
	"USA": 328.2e6
}
DAYOFFSET = 31
ref_date = datetime.date(2020, 1, 22)
colors = {
	"Germany": "black",
	"Switzerland": "grey",
	"Italy": "seagreen",
	"France": "mediumblue",
	"UK": "red",
	"USA": "sandybrown"
}

#read the data
data_infected = pd.read_csv(data_path_infected, header=0, sep=",").drop(["Lat", "Long"], axis=1)
data_deaths = pd.read_csv(data_path_deaths, header=0, sep=",").drop(["Lat", "Long"], axis=1)
data_recovered = pd.read_csv(data_path_recovered, header=0, sep=",").drop(["Lat", "Long"], axis=1)

#convert dates to day differences
date_format = "(?P<month>[0-9]*)/(?P<day>[0-9]*)/(?P<year>[0-9]*)"

date_mapping = {}
for datestr in data_infected:
	match = re.search(date_format, datestr)
	if match is None:		#only convert dates
		continue
	day = int(match.group("day"))
	month = int(match.group("month"))
	year = 2000+int(match.group("year"))
	this_date = datetime.date(year, month, day)
	delta_days = (this_date-ref_date).days
	date_mapping[datestr] = delta_days

#preprocess / clear data
data_infected=data_infected.rename(columns=date_mapping)
data_deaths=data_deaths.rename(columns=date_mapping)
data_recovered=data_recovered.rename(columns=date_mapping)

data_infected_byCountry = {}
data_deaths_byCountry = {}
data_recovered_byCountry = {}
for d, m in [(data_infected, data_infected_byCountry), (data_deaths, data_deaths_byCountry), (data_recovered, data_recovered_byCountry)]:
	m["Germany"] = d[(d["Country/Region"]=="Germany")]
	m["Italy"] = d[(d["Country/Region"]=="Italy")]
	m["France"] = d[(d["Country/Region"]=="France") & (d["Province/State"].isnull())]
	m["UK"] = d[(d["Country/Region"]=="United Kingdom") & (d["Province/State"].isnull())]
	m["USA"] = d[(d["Country/Region"]=="US")]
	m["Switzerland"] = d[(d["Country/Region"]=="Switzerland")]

for country in data_infected_byCountry:
	data_infected_byCountry[country] = data_infected_byCountry[country].drop(["Province/State", "Country/Region"], axis=1)
	data_deaths_byCountry[country] = data_deaths_byCountry[country].drop(["Province/State", "Country/Region"], axis=1)
	data_recovered_byCountry[country] = data_recovered_byCountry[country].drop(["Province/State", "Country/Region"], axis=1)
	

#compute restriction dates:
for country in restriction_dates:
	restriction_dates[country] = (restriction_dates[country]-ref_date).days

#get all dates
all_days = []
for day in data_infected_byCountry["Switzerland"]:
	if day<DAYOFFSET:
		continue
	all_days.append(day)

#to make video out of it
plot_list = []
for max_day in all_days:
	plt_path = os.path.abspath("day%i.png"%max_day)
	if os.path.exists(plt_path):
		plot_list.append(plt_path)
		continue

	#draw graphics
	for drawindex, country in enumerate(["Switzerland", "Italy", "Germany",  "France", "UK", "USA"]):
		days = []
		infected = []
		deaths = []
		recovered = []
		for day in data_infected_byCountry[country]:
			if day>max_day:
				continue
			days.append(day-DAYOFFSET)
			try:
				infected.append(np.array(data_infected_byCountry[country][day])[0])
				deaths.append(np.array(data_deaths_byCountry[country][day])[0]*100000./population[country])
				recovered.append(np.array(data_recovered_byCountry[country][day])[0])
			except:
				import pdb
				pdb.set_trace()


		N_infected = max(deaths)
		#infected = 100.*np.array(infected)/N_infected
		deaths = np.array(deaths)
		#recovered = 100.*np.array(recovered)/N_infected

		#plt.plot(days, infected, color=colors[country], linewidth=2, linestyle="solid")
		plt.plot(days, deaths, color=colors[country], linewidth=3, linestyle="solid", label="%s: %.1f" % (country, max(deaths)))
		#plt.plot(days, recovered, color=colors[country], linewidth=2, linestyle="dotted")
		#plt.text((drawindex%3)*0.33*(max_day-DAYOFFSET+1), 115-5.*(drawindex/3), "%s, %i infected"%(country, N_infected), color=colors[country], family="monospace", fontsize=10)
		updated_date = ref_date+datetime.timedelta(days=DAYOFFSET)+datetime.timedelta(days=max(days))
		updated_date.strftime("%d/%m/%Y")
		plt.text(0, -10, "Last update: "+str(updated_date), fontsize=14)

	'''
	#plot travel restriction / shutdown lines
	for country in restriction_dates:
		if restriction_dates[country]<=max_day:
			plt.axvline(restriction_dates[country]-0.1, ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")
			plt.axvline(restriction_dates[country], ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")
			plt.axvline(restriction_dates[country]+0.1, ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")
	'''

	plt.text((max_day-DAYOFFSET+1)*1.03, 40., "Data taken from:", rotation=90, family="monospace", fontsize=12, color="black")
	plt.text((max_day-DAYOFFSET+1)*1.06, 0., "https://data.humdata.org/dataset/novel-coronavirus-2019-ncov-cases", rotation=90, family="monospace", fontsize=10, color="black")
	plt.legend(loc="upper left", fontsize=16)

	plt.xlim(0., max_day-DAYOFFSET+1)
	plt.xlabel("#Days after 22 Feb 2020", fontsize=18)
	plt.ylabel("Number of Covid-19-related deaths / 100,000 inhabitants", fontsize=18)
	plot_list.append(plt_path)
	print("Saving",plt_path)
	plt.savefig(plt_path)
	plt.clf()



import imageio
print("Transforming to video")
with imageio.get_writer('covid19_spread.mp4', fps=4) as writer:
    for im in plot_list:
        writer.append_data(imageio.imread(im))
    writer.close()
