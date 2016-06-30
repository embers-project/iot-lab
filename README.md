# IoT-LAB EMBERS project 

This repository is an IoT-LAB SDK for the H2020 [EMBERS](http://www.embers-project.eu/) project. It provides a set of tools for developers to run efficiently experimentation tests. 


### Requirement

* Create an [IoT-LAB](https://www.iot-lab.info/testbed/signup.php) testbed account

### Launch an experiment

The first step is to launch an experiment on the IoT-LAB testbed. For this purpose you must choose :
  * an [IoT-LAB site](https://www.iot-lab.info/deployment/)
  * the experiment duration
  * which wireless sensors device you will book
  * (Optionnally) a firmware to flash on the sensors.

You can easily do this action with IoT-LAB [command-line tools](https://www.iot-lab.info/tutorials/experiment-cli-client/) (CLI) installed on each IoT-LAB site frontend SSH.

Go to the frontend SSH
  ```  
  my_computer$ ssh <login>@<site>.iot-lab.info
  <login>@<site>:~$ 
  ```
Configure IoT-LAB authentication and verify your credentials (print sensors list)
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
