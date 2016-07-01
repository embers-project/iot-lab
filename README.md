# IoT-LAB EMBERS project 

This repository is an IoT-LAB SDK for the H2020 [EMBERS](http://www.embers-project.eu/) project. It provides a set of tools for developers to run efficiently experimentation tests. 

### Requirement

* Ask an [IoT-LAB](https://www.iot-lab.info/testbed/signup.php) testbed account

### Launch testbed experiment

The first step is to launch an experiment on the IoT-LAB testbed. For this purpose you must choose :
  * an [IoT-LAB site](https://www.iot-lab.info/deployment/)
  * the experiment duration
  * which nodes you will book
  * (Optionnally) a firmware to flash on the nodes.

You can easily do this action with IoT-LAB [command-line tools](https://www.iot-lab.info/tutorials/experiment-cli-client/) (cli-tools) installed on each IoT-LAB site frontend SSH.

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
  
  # duration = 30 minutes / 4 M3 nodes : m3-[1,4,5,6].<site>.iot-lab.info / firmware embers_sensors.elf
  <login>@<site>:~$ experiment-cli submit -d 30 -l <site>,m3,1+4-6,embers_sensors.elf
  ```

### Launch M2M device broker test

You must clone this repository on the frontend SSH

 ```  
 <login>@<site>:~$ git clone https://github.com/embers-project/iot-lab.git
 <login>@<site>:~$ cd iot-lab
 ``` 
We provide you a binary firmware file (eg. firmwares/embers_sensors.elf) in charge of reading sensors values (eg. light, temperature, pressure) and emulate parking event. In this test you must use <b>M3 nodes</b> and you can view sensors hardware specification [here](https://www.iot-lab.info/hardware/m3/). The parking event emulation is based on a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution).

You can view the firmware [source code](https://github.com/iot-lab/openlab/tree/master/appli/iotlab_examples/embers_sensors) and how to modify and compile it [here](https://www.iot-lab.info/tutorials/get-compile-a-m3-firmware-code/). It's based on IoT-LAB [OpenLAB](https://github.com/iot-lab/openlab) drivers and [FreeRTOS](http://www.freertos.org/) embedded operating system. 

This firmware is configurable (eg. start measure with a period) by serial communication. Indeed on the frontend SSH when the experiment is running you can access all experiment nodes serial port (tcp socket on port 20000) and send commands to the firmware. Moreover the sensors and parking event data is written on the serial port. We use an IoT-LAB library, [serial_aggregator](https://www.iot-lab.info/tutorials/nodes-serial-link-aggregation/), to aggregate all the experiment nodes serial links (python script based on the cli-tools and asyncore events). When we received measures data from serial links nodes we just send it to the broker device.

Verify that your experiment is running :

```  
<login>@<site>:~/iot-lab$ experiment-cli wait
Waiting that experiment <exp_id> gets in state Running
"Running"
``` 

If you don't launch an experiment with firmware you can simply flash the firmware on all experiments nodes :

 ```  
 <login>@<site>:~/iot-lab$ node-cli --update firmwares/embers_sensors.elf
 ``` 

Currently you can only test a [Meshblu](https://meshblu.readme.io/) device broker implementation with HTTP protocol. You must fill the broker file configuration and meshblu section (url and gateway uuid parameters).

```
<login>@<site>:~/iot-lab$ cat broker.cfg
[meshblu]
url= 
gateway_uuid=
``` 

Finally you can launch Meshblu device broker test as follows :

```
<login>@<site>:~/iot-lab$ ./serial_nodes.py -h
# read sensors with a period of 10 seconds
<login>@<site>:~/iot-lab$ ./serial_nodes.py --sensors-period 10
# parking event with a period of 30 seconds (eg. average of 1 event every 30 seconds or 120 events per hour) 
<login>@<site>:~/iot-lab$ ./serial_nodes.py --sensors-parking 30
# read sensors and parking event at the same time
<login>@<site>:~/iot-lab$ ./serial_nodes.py --sensors-period 10 --sensors-parking 30
``` 

It's an interactive script execution and you can stop manually the execution with Ctrl+C shortcut.
At the end of the experiment the script will also ended automatically due to serial_aggregator library detection.

If you want a non interactive execution you can use this command :

```
# killed automatically at the end of experiment
<login>@<site>:~/iot-lab$ nohup ./serial_devices.py --sensors-period 10 > embers_sensors.log 2>&1 &
``` 

Congratulations, you launch your first test !!!!









