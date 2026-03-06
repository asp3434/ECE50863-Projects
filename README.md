# Computer Network Systems (ECE50863-Projects)
This is a repository for my projects in ECE50863 - Computer Network Systems at Purdue University.

### Lab 1: Network Topology - Dijkstra's Algorithm - Sockets - Multithreading
#### Description
An implementation of Dijkstra's algorithm to establish a shortest-path network topology given changing link states. This is a "centralized" method of identifying routes, using a single controller to make routing decisions.

#### Details
Controller: Sends out topology updates based on reports from each switch. E.g., link failed states.

Switch: Sends periodic messages to neighboring switches to inform them that it is still alive. If a link fails, it reports it to the controller. Receives updates from the controller to choose new packet routes as needed.

socket: Each switch instance (specified using the CLI, but using the same switch.py script) has a socket to communicate with other switches and the controller.

multi-threading: Used to perform "listening" and "working" functions simultaneously.

### Lab 2: Adaptive Bitrate Algorithms (ABRs)
#### Description
Three ABRs to provide the best Quality of Experience (QoE) for a simulated video with simulated chunk sizes and network throughput.

#### Details
Buffer-Based Approach (BBA): Selects quality level based on the size of the buffer (student1.py).

Robust Model Predictive Control (RobustMPC): Selects quality level by using the harmonic mean of previous throughputs to predict the throughput of the next "chunks" of video. Via a recursive function, the ABR identifies the highest possible QoE for x future chunks and based on the results, selects the corresponding quality level for the current chunk (student2.py).

customABR: A combination of BBA and RobustMPC that uses a target buffer size rather than buffer "reservoirs." Hysteresis is implemented around the target buffer size to use RobustMPC when within the acceptable range (student3.py).

### Lab 3: TBD
#### Description
TBD

#### Details
TBD