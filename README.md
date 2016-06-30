# IoT-LAB EMBERS project 

This repository is an IoT-LAB SDK for the H2020 [EMBERS](http://www.embers-project.eu/) project. It provides a set of tools for developers to run efficiently experimentation tests. 


### Requirement

* Create an [IoT-LAB](https://www.iot-lab.info/testbed/signup.php) testbed account

### Launch an experiment

The first step is to launch an experiment on the IoT-LAB testbed. For this purpose you must choose :
  * an [IoT-LAB site](https://www.iot-lab.info/deployment/)
  * the experiment duration
  * which nodes you will book
  * (Optionnally) a firmware to flash on the nodes.

You can easily do this action with IoT-LAB [command-line tools](https://www.iot-lab.info/tutorials/experiment-cli-client/) (cli-tools) installed on each IoT-LAB site frontend SSH.

Go to the frontend SSH
  ```  
  my_computer$ ssh <login>@<site>.iot-lab.info
  <login>@<site>:~$ 
  ```
Configure IoT-LAB authentication and verify your credentials (print nodes list)
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
We provide you a binary firmware file (eg. firmwares/embers_sensors.elf) in charge of reading sensors values (eg. light, temperature, pressure) and emulate parking event. In this example we use M3 nodes and you can view sensors hardware specification [here](https://www.iot-lab.info/hardware/m3/). The parking event emulation is based on a [Poisson distribution](https://en.wikipedia.org/wiki/Poisson_distribution). 

This firmware is configurable (eg. start measure with a period) by serial communication. Indeed on the frontend SSH when the experiment is running you can access all experiment nodes serial port (tcp socket on port 20000) and send commands to the firmware. Moreover the sensors and parking event data is written on the serial port. We use an IoT-LAB library, [serial_aggregator](https://www.iot-lab.info/tutorials/nodes-serial-link-aggregation/), to aggregate all the experiment nodes serial links (python script based on the cli-tools and asyncore events)

Currently you can only test a [Meshblu](https://meshblu.readme.io/) device broker implementation. You must fill the broker file configuration and the meshblu section.

```  
 <login>@<site>:~$ git clone https://github.com/embers-project/iot-lab.git
 <login>@<site>:~$ cd iot-lab
 ``` 






