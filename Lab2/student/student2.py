from typing import List
import matplotlib.pyplot as plt
import statistics

# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================


class ClientMessage:
	"""
	This class will be filled out and passed to student_entrypoint for your algorithm.
	"""
	total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
	previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

	buffer_current_fill: float		    # The number of kB currently in the client buffer
	buffer_seconds_per_chunk: float     # Number of seconds that it takes the client to watch a chunk. Every
										# buffer_seconds_per_chunk, a chunk is consumed from the client buffer.
	buffer_seconds_until_empty: float   # The number of seconds of video left in the client buffer. A chunk must
										# be finished downloading before this time to avoid a rebuffer event.
	buffer_max_size: float              # The maximum size of the client buffer. If the client buffer is filled beyond
										# maximum, then download will be throttled until the buffer is no longer full

	# The quality bitrates are formatted as follows:
	#
	#   quality_levels is an integer reflecting the # of quality levels you may choose from.
	#
	#   quality_bitrates is a list of floats specifying the number of kilobytes the upcoming chunk is at each quality
	#   level. Quality level 2 always costs twice as much as quality level 1, quality level 3 is twice as big as 2, and
	#   so on.
	#       quality_bitrates[0] = kB cost for quality level 1
	#       quality_bitrates[1] = kB cost for quality level 2
	#       ...
	#
	#   upcoming_quality_bitrates is a list of quality_bitrates for future chunks. Each entry is a list of
	#   quality_bitrates that will be used for an upcoming chunk. Use this for algorithms that look forward multiple
	#   chunks in the future. Will shrink and eventually become empty as streaming approaches the end of the video.
	#       upcoming_quality_bitrates[0]: Will be used for quality_bitrates in the next student_entrypoint call
	#       upcoming_quality_bitrates[1]: Will be used for quality_bitrates in the student_entrypoint call after that
	#       ...
	#
	quality_levels: int
	quality_bitrates: List[float]
	upcoming_quality_bitrates: List[List[float]]

	# You may use these to tune your algorithm to each user case! Remember, you can and should change these in the
	# config files to simulate different clients!
	#
	#   User Quality of Experience =    (Average chunk quality) * (Quality Coefficient) +
	#                                   -(Number of changes in chunk quality) * (Variation Coefficient)
	#                                   -(Amount of time spent rebuffering) * (Rebuffering Coefficient)
	#
	#   *QoE is then divided by total number of chunks
	#
	quality_coefficient: float
	variation_coefficient: float
	rebuffering_coefficient: float
# ======================================================================================================================


# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.
rebuffer_array = []
buffer_size_array = []
bitrate_array = []
bitrate_choice_array = []
throughput_array = []
qoe_array = []
time_array = []

window: int

def MPC(message: ClientMessage):
    global bitrate_choice_array
    global bitrate_array
    
    # start things off
    if message.previous_throughput == 0:
        
        bitrate_choice_array.append(0)
        bitrate = message.quality_bitrates[0]
        bitrate_array.append(bitrate)
        return message.quality_bitrates[0]
    
    else:
        

def update_arrays(message: ClientMessage):
    global rebuffer_array
    global buffer_size_array
    global bitrate_array
    global throughput_array
    global time_array
    
    # update time array
    time_array.append(message.total_seconds_elapsed)
    
    # number of chunks in the buffer    
    chunk_buffer_fill = message.buffer_seconds_until_empty / message.buffer_seconds_per_chunk
    
    # update rebuffer event array, kB
    if chunk_buffer_fill == 0 or message.buffer_seconds_until_empty < message.buffer_seconds_per_chunk:
        rebuffer_array.append(1)
    else:
        rebuffer_array.append(0)
        
    # update buffer size array
    buffer_size_array.append(chunk_buffer_fill)
    
    # update throughput array
    throughput_array.append(message.previous_throughput)
    
# def update_qoe_array():

def plot_buffer_size():
    plt.figure()
    
    # plot the buffer
    plt.plot(time_array, buffer_size_array, label="Buffer")
    
    #plot rebuffer events
    for i in range(len(rebuffer_array)):
        if rebuffer_array[i]:
            plt.axvline(x= time_array[i], color="red")
            
    plt.xlabel("Time (s)")
    plt.ylabel("Buffer Size (kB)")
    plt.title("Buffer Size vs Time")
    
    plt.savefig("MPC_buffer_size.png")
    plt.close()
    
def plot_bitrate():
    plt.figure()
    
    # plot the bitrate
    plt.plot(time_array, bitrate_array, label="Bitrate")
        
    # labels and title
    plt.xlabel("Time (s)")
    plt.ylabel("Bitrate / Quality (kB)")
    plt.title("Bitrate / Quality vs Time")
    
    plt.savefig("MPC_bitrate_quality.png")
    plt.close()
    
def plot_throughput():
    plt.figure()
    
    # plot the throughput
    plt.plot(time_array, throughput_array, label="Throughput")
        
    # labels and title
    plt.xlabel("Time (s)")
    plt.ylabel("Throughput (kB/s)")
    plt.title("Throughput vs Time")
    
    plt.savefig("MPC_throughput.png")
    plt.close()

# def plot_qoe():

def student_entrypoint(client_message: ClientMessage):
    
    update_arrays(client_message)
    quality = MPC(client_message)
    
    if len(client_message.upcoming_quality_bitrates) == 0:
        plot_buffer_size()
        plot_bitrate()
        plot_throughput()
        
    return quality  # Let's see what happens if we select the highest bitrate every time
