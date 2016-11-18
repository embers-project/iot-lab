# IoT-LAB EMBERS project 

This repository contains an SDK for the H2020 [EMBERS](http://www.embers-project.eu/) project. It provides a set of tools for developers to run efficiently experimentation tests from the IoT-Lab. 

## Requirement

* Ask for an [IoT-LAB](https://www.iot-lab.info/testbed/signup.php) testbed account

## Launch testbed experiment

The first step is to launch an experiment on the IoT-LAB testbed. For this purpose you must choose:
  * an [IoT-LAB site](https://www.iot-lab.info/deployment/)
  * the experiment duration
  * which nodes you will book

You can easily do this action with IoT-LAB [command-line tools](https://www.iot-lab.info/tutorials/experiment-cli-client/) (CLI-tools) installed on each IoT-LAB site frontend SSH.

Go to the frontend SSH site
  ```  
  my_computer$ ssh <login>@<site>.iot-lab.info
  <login>@<site>:~$ 
  ```
Configure IoT-LAB authentication and verify your credentials (print IoT-LAB site nodes list)
  ```  
  <login>@<site>:~$ auth-cli -u <login>
  <login>@<site>:~$ experiment-cli info -l --site <site>
  ``` 
Launch an experiment 
  ```
  # duration = 60 minutes / 100 M3 nodes : thanks to the scheduler which automatically choose nodes for you
  <login>@<site>:~$ experiment-cli submit -d 60 -l 100,archi=m3:at86rf231+site=<site>
  
  # duration = 120 minutes / 50 M3 nodes : m3-1.<site>.iot-lab.info to m3-50.<site>.iot-lab.info
  <login>@<site>:~$ experiment-cli submit -d 120 -l <site>,m3,1-50
  ```

## Launch M2M device broker test

### Manual execution

You must clone this repository on the frontend SSH

 ```
 <login>@<site>:~$ mkdir embers && cd embers
 <login>@<site>:~/embers$ git clone https://github.com/embers-project/iot-lab.git
 <login>@<site>:~/embers$ cd iot-lab
 ``` 
We provide you a binary firmware example (e.g. `firmwares/embers_sensors.elf`) in charge of reading sensor values (e.g. light, temperature, pressure) and simulate parking events. In this test you must use <b>M3 nodes</b> (you can view sensors hardware specification [here](https://www.iot-lab.info/hardware/m3/)), and the parking event simulation is based on a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution).

You can view the firmware [source code](https://github.com/iot-lab/openlab/tree/master/appli/iotlab_examples/embers_sensors) and how to modify and compile it [here](https://www.iot-lab.info/tutorials/get-compile-a-m3-firmware-code/). It's based on IoT-LAB [OpenLAB](https://github.com/iot-lab/openlab) drivers and [FreeRTOS](http://www.freertos.org/) embedded operating system. 

This firmware is configurable (e.g. start measurement with a period) by serial communication. Indeed, on the frontend SSH when the experiment is running you can access all experiment nodes serial port (TCP socket on port 20000) and send commands to the firmware. Moreover the sensors and parking event data is written on the serial port.

Verify that your experiment is running and flash firmware on all experiment nodes :

```  
<login>@<site>:~/embers/iot-lab$ experiment-cli wait
Waiting that experiment <exp_id> gets in state Running
"Running"
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --flash
``` 
You should test the firmware execution on one experiment node. After the netcat command (e.g. nc) you
type Enter and print the firmware usage. Next we start sensors measure with "**sensors_on**" and stop
it with "**sensors_off**" character string. 

```  
<login>@<site>:~/embers/iot-lab$ nc m3-<id> 20000
Command              Description
--------------------------------
help                 Print this help
sensors_on           [delay:seconds] Start sensors measure. Default 5s, min 1s
sensors_off          Stop sensors measure
parking_on           [average delay:seconds] Start parking simulator. Default 30s, min 1s
parking_off          Stop parking simulator
traffic              [vehicle count]  Send traffic event
random_on            Add a random delay before starting measures, default ON
random_off           No random delay before starting measures.
--------------------------------
sensors_on
{"temperature":3.625833E1,"luminosity":1.171875E2,"pressure":9.8937866E2}
{"temperature":3.628125E1,"luminosity":1.1694336E2,"pressure":9.893745E2}
{"temperature":3.6260418E1,"luminosity":1.171875E2,"pressure":9.894043E2}
sensors_off
``` 

Finally you can launch device broker test with [serial_sensors.py](https://github.com/emberscity/iot-lab/blob/master/serial_sensors.py) script. This script will automatically get your experiment nodes list and flash the firmare with CLI-tools library. We also use an IoT-LAB  [Serial Aggregator](https://www.iot-lab.info/tutorials/nodes-serial-link-aggregation/) library, to aggregate all the experiment nodes serial links. Thus the script sends the measurement configuration and receives measures data by serial nodes communication. The last stage is the interaction with the device broker like register/unregister devices or send the measurement data.

Actually you can only test a [Meshblu](https://meshblu.readme.io/) device broker implementation with HTTP protocol. You must fill the broker file configuration and Meshblu section (URL and Gateway UUID parameters).

```
<login>@<site>:~/embers/iot-lab$ cat broker.cfg
[meshblu]
url= 
gateway_uuid=
``` 
Finally you should launch the serial_sensors.py script as follows :

```
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py -h
# read iotlab sensors with a period of 10 seconds
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --iotlab-sensors 10
# parking event with a period of 30 seconds (eg. average of 1 event every 30 seconds or 120 events per hour) 
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --parking 30
# traffic events read from dataset every 5 seconds
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --traffic
# pollution events read from dataset every 5 minutes
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --pollution
``` 

> If you have many experiments launch at the same time you must specify the experiment id with -i &lt;exp_id&gt; option.

Note: for --traffic to work, un-tar the dataset in `datasets/citypulse/`
      with the following command: `tar xf traffic_feb_jun_2014.tar.bz2`
      as a one-time operation.

It's an interactive script execution and you can stop manually the execution with Ctrl+C shortcut.
At the end of the experiment the script will also have ended automatically due to `serial_aggregator` library detection.

If you want a non interactive execution you can use this command :

```
# killed automatically at the end of experiment
<login>@<site>:~/embers/iot-lab$ ./serial_sensors.py --sensors 10 &> embers_sensors.log < /dev/null &
```

Congratulations, you've succesfully launched your first test!


### Automatic execution

You can launch automatically the script serial_sensors.py on the frontend SSH with IoT-LAB REST API and CLI-tools. You can find in the directory scripts of this repository a [run_serial_sensors](https://github.com/emberscity/iot-lab/blob/master/scripts/run_serial_sensors) script example. You must fill the measurement data and device broker configuration variables inside this script.

```
#########################
# Script configuration  #
#######################################################

# Measurement configuration
SENSORS_PERIOD=10
# Not activate by default
PARKING_PERIOD=

# Meshblu device broker configuration 
BROKER_URL=""
GATEWAY_UUID=""
```
Next you should launch this script as follows:

```
<site> = IoT-LAB site where you run your experiment
<login>@<site>:~/embers/iot-lab$ experiment-cli script --run scripts/run_serial_sensors,<site>
```
> The run_serial_sensors script writes an execution log file &lt;exp_id&lt;.log in the embers directory of your home directory on the frontend SSH.

The IoT-LAB testbed execute your script on the frontend SSH site in a [screen](https://www.gnu.org/software/screen/manual/screen.html) session with your user identity. You can visualize the screen session as well during the script execution.

```
s<login>@<site>:~/embers/iot-lab$ screen -ls
There is a screen on:
	536.<exp_id>-<login>	(12/10/2016 10:49:12)	(Detached)
1 Socket in /var/run/screen/S-<login>.
```
You can also control the status of the script execution and stop it manually. At the end of the experiment when we receive a stop experiment request by the scheduler if a script is running it will be killed automatically.

```
<login>@<site>:~/embers/iot-lab$ experiment-cli script --status
<login>@<site>:~/embers/iot-lab$ experiment-cli script --kill
```

If you happen to face any problem with these tools, feel free to create an issue [here](https://github.com/embers-project/iot-lab/issues) or in our [Support Forum](http://support.embers.city/)
