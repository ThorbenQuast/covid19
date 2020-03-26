import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt

import os, re, datetime

data_path_infected = os.path.abspath("data/time_series_covid19_confirmed_global.csv")
data_path_deaths = os.path.abspath("data/time_series_covid19_deaths_global.csv")
restriction_dates = {
	"Hubei": datetime.date(2020, 1, 30),
	"Italy": datetime.date(2020, 3, 12),
	"France": datetime.date(2020, 3, 17),
	"Germany": datetime.date(2020, 3, 22),
	"UK": datetime.date(2020, 3, 24),
}
ref_date = datetime.date(2020, 1, 22)
colors = {
	"Germany": "black",
	"Hubei": "grey",
	"Italy": "seagreen",
	"France": "mediumblue",
	"UK": "red",
	"USA": "sandybrown"
}


#read the data
data_infected = pd.read_csv(data_path_infected, header=0, sep=",").drop(["Lat", "Long"], axis=1)
data_deaths = pd.read_csv(data_path_deaths, header=0, sep=",").drop(["Lat", "Long"], axis=1)

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

data_infected_byCountry = {}
data_deaths_byCountry = {}
for d, m in [(data_infected, data_infected_byCountry), (data_deaths, data_deaths_byCountry)]:
	m["Germany"] = d[(d["Country/Region"]=="Germany")]
	m["Italy"] = d[(d["Country/Region"]=="Italy")]
	m["France"] = d[(d["Country/Region"]=="France") & (d["Province/State"].isnull())]
	m["UK"] = d[(d["Country/Region"]=="United Kingdom") & (d["Province/State"].isnull())]
	m["USA"] = d[(d["Country/Region"]=="US")]
	m["Hubei"] = d[(d["Country/Region"]=="China") & (d["Province/State"]=="Hubei")]

for country in data_infected_byCountry:
	data_infected_byCountry[country] = data_infected_byCountry[country].drop(["Province/State", "Country/Region"], axis=1)
	data_deaths_byCountry[country] = data_deaths_byCountry[country].drop(["Province/State", "Country/Region"], axis=1)
	

#compute restriction dates:
for country in restriction_dates:
	restriction_dates[country] = (restriction_dates[country]-ref_date).days

#get all dates
all_days = []
for day in data_infected_byCountry["Hubei"]:
	if day<5:
		continue
	all_days.append(day)

#to make video out of it
plot_list = []
for max_day in all_days:
	#draw graphics
	for drawindex, country in enumerate(["Hubei", "Italy", "Germany",  "France", "UK", "USA"]):
		days = []
		infected = []
		deaths = []
		for day in data_infected_byCountry[country]:
			if day>max_day:
				continue
			days.append(day)
			try:
				infected.append(np.array(data_infected_byCountry[country][day])[0])
				deaths.append(np.array(data_deaths_byCountry[country][day])[0])
			except:
				import pdb
				pdb.set_trace()


		N_infected = max(infected)
		infected = 100.*np.array(infected)/N_infected
		deaths = 100.*np.array(deaths)/N_infected
		plt.plot(days, infected, color=colors[country], linewidth=2, linestyle="solid")
		plt.plot(days, deaths, color=colors[country], linewidth=2, linestyle="dashed")
		plt.text((drawindex%3)*0.33*max_day, 108-5.*(drawindex/3), "%s, %i infected"%(country, N_infected), color=colors[country], family="monospace", fontsize=10)
		updated_date = ref_date+datetime.timedelta(days=max(days))
		updated_date.strftime("%d/%m/%Y")
		plt.text(-max_day*0.05, -10, updated_date)

	#plot travel restriction / shutdown lines
	for country in restriction_dates:
		if restriction_dates[country]<=max_day:
			plt.axvline(restriction_dates[country]-0.1, ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")
			plt.axvline(restriction_dates[country], ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")
			plt.axvline(restriction_dates[country]+0.1, ymin=-0., ymax=0.05, color=colors[country], linewidth=1, linestyle="solid")

	plt.text(max_day*1.03, 40., "Source:", rotation=90, family="monospace", fontsize=10, color="black")
	plt.text(max_day*1.06, 105., "https://data.humdata.org/dataset/novel-coronavirus-2019-ncov-cases", rotation=90, family="monospace", fontsize=10, color="black")
	plt.plot(days, np.zeros(len(days)), color="black", linestyle="solid", label="infected")
	plt.plot(days, np.zeros(len(days)), color="black", linestyle="dashed", label="dead")
	#plt.plot(days, np.zeros(len(days)), color="black", linestyle="dotted", label="recovered")
	plt.legend(loc="upper left")

	plt.xlim(0., max_day)
	plt.xlabel("#Days after 22 Jan 2020")
	plt.ylabel("Fraction of total infected in country/region [x100]")
	plt_path = os.path.abspath("day%i.png"%max_day)
	plot_list.append(plt_path)
	print "Saving",plt_path
	plt.savefig(plt_path)
	plt.clf()


import imageio
print "Transforming to video"
with imageio.get_writer('covid19_spread.mp4', fps=4) as writer:
    for im in plot_list:
        writer.append_data(imageio.imread(im))
    writer.close()
