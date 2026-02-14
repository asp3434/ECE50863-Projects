from typing import List
# import matplotlib.pyplot as plt
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
time_array = []

golden_qoe_array = []

window: int
num_chunks: int

def MPC(message: ClientMessage):
    global window
    global num_chunks
    global golden_qoe_array
    
    # start things off
    if len(time_array) <= 1:
        window = 5
        num_chunks = len(message.upcoming_quality_bitrates) + 1
        
        update_bitrate_array(message, 0)
        return 0
    
    else:
        n = 0
        qoe = 0.00001
        
        c_qual = message.quality_coefficient
        c_var = message.variation_coefficient
        c_rebuff = message.rebuffering_coefficient
        c = [c_qual, c_var, c_rebuff]
        
        track = 0
        quality_level = 0
        for i, quality in enumerate(message.quality_bitrates):
            ## starting point for each quality
            seconds_to_download = quality / statistics.harmonic_mean(throughput_array[-5:])
            buffer_size = message.buffer_seconds_until_empty - seconds_to_download + message.buffer_seconds_per_chunk # measured in seconds
            
            variables = [quality, buffer_size, c, window, n]
            
            ## qoe arrays ##
            loop_quality_array = [quality]
            loop_qual_change_array = []
            loop_rebuffer_time_array = [0]
            
            qoe_arrays = [loop_quality_array, loop_qual_change_array, loop_rebuffer_time_array]
            
            ## other arrays ##
            loop_buffer_array = [buffer_size]
            loop_qual_choice_array = [i]
            
            ## the golden qoe array
            golden_qoe_array = []
            
            other_arrays = [loop_buffer_array, loop_qual_choice_array]
            
            ## enter the death loop, but only enter if we're not going to immediately rebuffer
            if seconds_to_download < message.buffer_seconds_until_empty:
                if i != bitrate_choice_array[-1]:
                    loop_qual_change_array.append(1)
                
                qoe_loop(message, variables, qoe_arrays, other_arrays)
                
                new_qoe = max(golden_qoe_array)
                if type(new_qoe) == list:
                    new_qoe = max(new_qoe)
                
                if new_qoe > qoe:
                    qoe = new_qoe
                    quality_level = i
            # if all options lead to rebuffering, just choose the lowest quality
            else:
                track += 1
                if track == message.quality_levels:
                    update_bitrate_array(message, 0)
                    return 0
        
        update_bitrate_array(message, quality_level)
        return quality_level
        
def qoe_loop(message:ClientMessage, v, qoe_arrays, other_arrays):
    global num_chunks
    global throughput_array
    global golden_qoe_array
    
    ## variables ##
    # quality = v[0]
    buffer_size = v[1]
    c = v[2]
    window = v[3]
    n = v[4]
    
    ## qoe arrays ##
    quality_array = qoe_arrays[0] # measured in number of chunks
    qual_change_array = qoe_arrays[1]
    rebuffer_time_array = qoe_arrays[2]
    
    ## other arrays ##
    buffer_array = other_arrays[0]
    qual_choice_array = other_arrays[1]
    
    if (n >= window) or (n >= len(message.upcoming_quality_bitrates)):
        qual = sum(quality_array)
        variability = sum(qual_change_array)
        rebuff_time = sum(rebuffer_time_array)
        
        qoe = (c[0] * qual - c[1] * variability - c[2] * rebuff_time)  / window
        
        qoe_arrays = [[] for row in qoe_arrays]
        other_arrays = [[] for row in other_arrays]
        
        golden_qoe_array.append(qoe)
    else:
                
        row = message.upcoming_quality_bitrates[n]
        for j, quality in enumerate(row):
            appended_rebuf = False
            appended_var = False
            
            seconds_to_download = quality / statistics.harmonic_mean(throughput_array[-5:])
            
            # update rebuff time
            if seconds_to_download > buffer_size:
                delta_rebuff = seconds_to_download - buffer_size
                rebuffer_time_array.append(delta_rebuff)
                appended_rebuf = True
            
            next_buffer_size = buffer_size - seconds_to_download + message.buffer_seconds_per_chunk # measured in seconds
            if next_buffer_size < 0:
                next_buffer_size = 0
            
            ## update variables
            v_next = v.copy()
            v_next[0] = quality
            v_next[1] = next_buffer_size
            v_next[4] = n +1
            
            ## update qoe arrays, except rebuff time
            quality_array.append(j) # update total quality

            if len(qual_choice_array) > 1:
                if j != qual_choice_array[-1]:
                    qual_change_array.append(1) # update quality change events
                    appended_var = True
            else:
                if j != qual_choice_array[0]:
                    qual_change_array.append(1) # update quality change events
                    appended_var = True
            
            ## update other arrays
            buffer_array.append(next_buffer_size)
            qual_choice_array.append(j)
                            
            qoe_arrays = [quality_array, qual_change_array, rebuffer_time_array]
            other_arrays = [buffer_array, qual_choice_array]
            
            qoe_loop(message, v_next, qoe_arrays, other_arrays)
            
            #cleanup the arrays after recursion
            qual_choice_array.pop()
            buffer_array.pop()
            quality_array.pop()

            if appended_var:
                qual_change_array.pop()

            if appended_rebuf:
                rebuffer_time_array.pop()

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
    if len(time_array) > 1:
        throughput_array.append(message.previous_throughput)
    
def update_bitrate_array(message: ClientMessage, quality_level):
    global bitrate_choice_array
    global bitrate_array
    
    bitrate_choice_array.append(quality_level)
    bitrate = message.quality_bitrates[quality_level]
    bitrate_array.append(bitrate)

# def plot_buffer_size():
#     plt.figure()
    
#     # plot the buffer
#     plt.plot(time_array, buffer_size_array, label="Buffer")
    
#     #plot rebuffer events
#     for i in range(len(rebuffer_array)):
#         if rebuffer_array[i]:
#             plt.axvline(x= time_array[i], color="red")
            
#     plt.xlabel("Time (s)")
#     plt.ylabel("Buffer Size (kB)")
#     plt.title("Buffer Size vs Time")
    
#     plt.savefig("MPC_buffer_size.png")
#     plt.close()
    
# def plot_bitrate():
#     plt.figure()
    
#     # plot the bitrate
#     plt.plot(time_array, bitrate_array, label="Bitrate")
        
#     # labels and title
#     plt.xlabel("Time (s)")
#     plt.ylabel("Bitrate / Quality (kB)")
#     plt.title("Bitrate / Quality vs Time")
    
#     plt.savefig("MPC_bitrate_quality.png")
#     plt.close()
    
# def plot_throughput():
#     plt.figure()
    
#     # plot the throughput
#     plt.plot(time_array, throughput_array, label="Throughput")
        
#     # labels and title
#     plt.xlabel("Time (s)")
#     plt.ylabel("Throughput (kB/s)")
#     plt.title("Throughput vs Time")
    
#     plt.savefig("MPC_throughput.png")
#     plt.close()

def student_entrypoint(client_message: ClientMessage):
    global throughput_array
    
    update_arrays(client_message)
    quality = MPC(client_message)
    
    # if len(client_message.upcoming_quality_bitrates) == 0:
    #     throughput_array.append(client_message.previous_throughput)
    #     plot_buffer_size()
    #     plot_bitrate()
    #     plot_throughput()
        
    return quality  # Let's see what happens if we select the highest bitrate every time
