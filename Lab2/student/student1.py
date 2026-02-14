from typing import List
import statistics
# import matplotlib.pyplot as plt

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

base_res_high: float
base_res_low: float
window: int
res_high: int
res_low: int
startup_over_flag: int
q_startup = 0

def bba_2(message: ClientMessage):
    global time_array
    global base_res_high
    global base_res_low
    global window
    global res_high
    global res_low
    global startup_over_flag
    global bitrate_choice_array
    global bitrate_array
    global q_startup
    
    # number of chunks in the buffer    
    chunk_buffer_fill = message.buffer_seconds_until_empty / message.buffer_seconds_per_chunk
    
    # set reservoir high and low values and begin startup phase
    if len(time_array) <= 1:
        window = int(round(0.03 * len(message.upcoming_quality_bitrates)))
        base_res_high = int(round(0.1 * len(message.upcoming_quality_bitrates)))
        base_res_low = int(round(0.08 * len(message.upcoming_quality_bitrates)))
        
        startup_over_flag = 0
    
    # dynamic reservoir
    avg_chunk = 0
    max_chunk = 0
    if len(message.upcoming_quality_bitrates[:window]) > 0:
        for row in message.upcoming_quality_bitrates[:window]:
            avg_chunk += statistics.mean(row)
            proposed_max_chunk = max(row)
            if proposed_max_chunk > max_chunk:
                max_chunk = proposed_max_chunk
    
        avg_chunk = avg_chunk / len(message.upcoming_quality_bitrates[:window])
        dynamic_ratio = (max_chunk / avg_chunk) - 1
        
        if dynamic_ratio > 3:
            res_low = int(round(base_res_low * dynamic_ratio))
            
        elif dynamic_ratio < 0.7142857142857142:
            res_high = int(round(base_res_high * dynamic_ratio))
        else:
            res_high = base_res_high
            res_low = base_res_low
    else:
        res_high = base_res_high
        res_low = base_res_low
    
    # startup phase
    # break startup conditions
    if (chunk_buffer_fill >= res_high) or (len(time_array) >= 50):
        startup_over_flag = 1
        
    if len(buffer_size_array) >= 2:
        if (buffer_size_array[-1] < buffer_size_array[-2]):
            startup_over_flag = 1
    
    # actual startup phase    
    if startup_over_flag == 0:
        if len(time_array) <= 1:
            #return lowest bitrate until we have a couple in the buffer
            bitrate_choice_array.append(0)
            bitrate = message.quality_bitrates[0]
            bitrate_array.append(bitrate)
            return 0
        else:
            q_startup += 1
            q_startup = min(q_startup, message.quality_levels - 1)
            if throughput_safety_check(message, q_startup, res_high, res_low):
                q_startup = max(0, q_startup - 1)
            
            bitrate_choice_array.append(q_startup)
            bitrate = message.quality_bitrates[q_startup]
            bitrate_array.append(bitrate)
            return q_startup
            
            ## I accidentally found the max video quality for each step given the previous throughput
            ## I'm keeping this for notes for later
            
            # while proposed_quality < message.quality_levels:
            #     check = throughput_safety_check(message, proposed_quality)
            #     if not check:
            #         proposed_quality += 1
            #     else:
            #         quality = max(0, proposed_quality - 1)
                    
            #         bitrate_choice_array.append(quality)
            #         bitrate = message.quality_bitrates[quality]
            #         bitrate_array.append(bitrate)
                    
            #         return quality
            
            # bitrate_choice_array.append(proposed_quality -1)
            # bitrate = message.quality_bitrates[proposed_quality-1]
            # bitrate_array.append(bitrate)
            # return proposed_quality-1
                    
    else:
        #lowest bitrate for low buffer
        if chunk_buffer_fill < res_low:
            
            #append choice to an array
            bitrate_choice_array.append(0)
            
            #return lowest bitrate until we fill the reservoir
            bitrate = message.quality_bitrates[0]
            bitrate_array.append(bitrate)
            return 0
        
        #highest bitrate for filled buffer
        elif chunk_buffer_fill >= res_high:
            
            #propose the highest bitrate if the buffer is full
            proposed_quality = message.quality_levels - 1

            bitrate_choice_array.append(proposed_quality)
            bitrate = message.quality_bitrates[proposed_quality]
            bitrate_array.append(bitrate)
                
            return proposed_quality
        
        elif (bitrate_choice_array[-1] != bitrate_choice_array[-2]):
            bitrate_choice_array.append(bitrate_choice_array[-1])
            bitrate = message.quality_bitrates[bitrate_choice_array[-1]]
            bitrate_array.append(bitrate)
            
            return bitrate_choice_array[-1]
        
        else:
            #linear function for the cushion zone
            ramp_chunks = res_high - res_low
            proposed_quality = int(round((message.quality_levels - 1) * (chunk_buffer_fill - res_low) / ramp_chunks))
            
            # mapping to chunks rather than qualities
            m = (chunk_buffer_fill - res_low) / ramp_chunks
            proposed_chunk_size = message.quality_bitrates[0] + m*(message.quality_bitrates[-1] - message.quality_bitrates[0])
            
            for i, chunk in enumerate(message.quality_bitrates):
                if chunk <= proposed_chunk_size:
                    proposed_quality = i
                else:
                    break
            
            bitrate_choice_array.append(proposed_quality)
            bitrate = message.quality_bitrates[proposed_quality]
            bitrate_array.append(bitrate)

            return proposed_quality

def throughput_safety_check(message: ClientMessage, proposed_quality_choice, reservoir_high, reservoir_low):
    if message.previous_throughput == 0:
        return 1
    else:
        delta_buffer = message.buffer_seconds_per_chunk - (message.quality_bitrates[proposed_quality_choice] / message.previous_throughput)
        
        # calculate buffer factor
        ramp_chunks = reservoir_high - reservoir_low
        chunk_buffer_fill = message.buffer_seconds_until_empty / message.buffer_seconds_per_chunk
        factor = (chunk_buffer_fill - reservoir_low) / ramp_chunks * 0.875
        
        if delta_buffer <= max(0.5, factor) * message.buffer_seconds_per_chunk:
            # a 1 means that you hit the check and you shouldn't use the proposed quality because throughput was too low
            return 1  
        else:
            return 0

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
    
#     plt.savefig("BBA2_buffer_size.png")
#     plt.close()
    
# def plot_bitrate():
#     plt.figure()
    
#     # plot the bitrate
#     plt.plot(time_array, bitrate_array, label="Bitrate")
        
#     # labels and title
#     plt.xlabel("Time (s)")
#     plt.ylabel("Bitrate / Quality (kB)")
#     plt.title("Bitrate / Quality vs Time")
    
#     plt.savefig("BBA2_bitrate_quality.png")
#     plt.close()
    
# def plot_throughput():
#     plt.figure()
    
#     # plot the throughput
#     plt.plot(time_array, throughput_array, label="Throughput")
        
#     # labels and title
#     plt.xlabel("Time (s)")
#     plt.ylabel("Throughput (kB/s)")
#     plt.title("Throughput vs Time")
    
#     plt.savefig("BBA2_throughput.png")
#     plt.close()

# def plot_qoe():

def student_entrypoint(client_message: ClientMessage):
    
    update_arrays(client_message)
    quality = bba_2(client_message)
    
    # if len(client_message.upcoming_quality_bitrates) == 0:
    #     plot_buffer_size()
    #     plot_bitrate()
    #     plot_throughput()
    
    return quality  # Let's see what happens if we select the lowest bitrate every time
