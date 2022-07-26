# -*- coding: utf-8 -*-
"""An example: code for assessing video/audio/MEG synchronization.
    
    This script takes four files (fiff, audio, and two videos) and generates
    a bunch of pictures. Each picture describes a short piece of the
    recordings. The upper pane shows 3 consecutive video frames from the first
    file, the lower - from the second file. The central pane shows the
    corresponding pieces of audio and a single MEG channel.
    
    ---------------------------------------------------------------------------
    Author: Andrey Zhdanov
    Copyright (C) 2014 BioMag Laboratory, Helsinki University Central Hospital

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import PIL
import io
import matplotlib.pyplot as plt
import numpy as np
import mne
import pyvideomeg

VIDEO_FNAME_1 = '/home/andrey/data/LA/LA_wakeup01R_st_mc.video.dat'
VIDEO_FNAME_2 = '/home/andrey/data/LA/LA_wakeup01R_st_mc.video.dat'
AUDIO_FNAME = '/home/andrey/data/LA/LA_wakeup01R_st_mc.audio.dat'
MEG_FNAME = '/home/andrey/data/LA/LA_wakeup01R_st_mc.fif'

TIMING_CH = 'STI 006'
MEG_CH = 'STI 006'
FRAME_SZ = (640, 480)
OUT_FLDR = '/tmp'
WIND_WIDTH = 3  # in frames
DPI = 80    # used for rendering the traces

# Percentiles to be used for vertical scaling (to avoid problems caused by
# outlers). Should be a float between 0 and 100
SCALE_PRCTILE_AUDIO = 99.99
SCALE_PRCTILE_MEG = 99.99

#--------------------------------------------------------------------------
# Load the data
#
raw = mne.io.Raw(MEG_FNAME, allow_maxshield=True)

# load the timing channel
picks_timing = mne.pick_types(raw.info, meg=False, include=[TIMING_CH])
dt_timing = raw[picks_timing,:][0].squeeze()

# load the MEG channel
picks_meg = mne.pick_types(raw.info, meg=False, include=[MEG_CH])
meg = raw[picks_meg,:][0].squeeze()

# compute the timestamps for the MEG channel
meg_ts = pyvideomeg.comp_tstamps(dt_timing, raw.info['sfreq'])

vid_file_1 = pyvideomeg.VideoData(VIDEO_FNAME_1)
vid_file_2 = pyvideomeg.VideoData(VIDEO_FNAME_2)
aud_file = pyvideomeg.AudioData(AUDIO_FNAME)

audio, audio_ts = aud_file.format_audio()
audio = audio[0,:].squeeze()    # use only the first audio channel


#--------------------------------------------------------------------------
# Make the pics
#
plt.ioff()  # don't pop up the figure windows

ts_scale = np.diff(vid_file_1.ts).max() * (WIND_WIDTH+0.1)
meg_scale = np.percentile(np.abs(meg), SCALE_PRCTILE_MEG) * 1.1
aud_scale = np.percentile(np.abs(audio), SCALE_PRCTILE_AUDIO) * 1.1

for i in range(1+WIND_WIDTH, len(vid_file_1.ts)-(1+WIND_WIDTH)):
    res = PIL.Image.new('RGB', (FRAME_SZ[0]*3, (FRAME_SZ[1]*2)+(FRAME_SZ[1]*2//3)))
    
    #----------------------------------------------------------------------
    # Paste the frame images into the final figure
    #

    # paste 3 frames from the first video file
    im0 = PIL.Image.open(io.BytesIO(vid_file_1.get_frame(i-1)))
    im1 = PIL.Image.open(io.BytesIO(vid_file_1.get_frame(i)))
    im2 = PIL.Image.open(io.BytesIO(vid_file_1.get_frame(i+1)))
   
    res.paste(im0, (0,0))
    res.paste(im1, (FRAME_SZ[0],0))
    res.paste(im2, (FRAME_SZ[0]*2,0))
    
    # find the closest 3 frames from the second video
    vid2_indx_unsorted = np.argsort(np.abs(vid_file_2.ts - vid_file_1.ts[i]))[0:3]   # find the closest 3 frames
    vid2_indx = vid2_indx_unsorted[np.argsort(vid_file_2.ts[vid2_indx_unsorted])]   # order the 3 frames
    
    # paste 3 frames from the second video file
    im0 = PIL.Image.open(io.BytesIO(vid_file_2.get_frame(vid2_indx[0])))
    im1 = PIL.Image.open(io.BytesIO(vid_file_2.get_frame(vid2_indx[1])))
    im2 = PIL.Image.open(io.BytesIO(vid_file_2.get_frame(vid2_indx[2])))
   
    res.paste(im0, (0, FRAME_SZ[1]+(FRAME_SZ[1]*2//3)))
    res.paste(im1, (FRAME_SZ[0], FRAME_SZ[1]+(FRAME_SZ[1]*2//3)))
    res.paste(im2, (FRAME_SZ[0]*2, FRAME_SZ[1]+(FRAME_SZ[1]*2//3)))
    
    #----------------------------------------------------------------------
    # Render and paste the traces into the final figure
    # plot the traces
    min_ts = vid_file_1.ts[i] - ts_scale
    max_ts = vid_file_1.ts[i] + ts_scale
    
    fig = plt.figure()
    meg_indx = np.where((meg_ts > min_ts) & (meg_ts < max_ts))
    plt.plot(meg_ts[meg_indx], meg[meg_indx] / meg_scale, 'b')
    
    audio_indx = np.where((audio_ts > min_ts) & (audio_ts < max_ts))
    plt.plot(audio_ts[audio_indx], audio[audio_indx] / aud_scale, 'g')
    
    # mark the frame positions
    plt.plot(vid_file_1.ts[i-1]*np.ones(2), (0.5,1), 'k')
    plt.plot(vid_file_1.ts[i]*np.ones(2), (0.5,1), 'k')
    plt.plot(vid_file_1.ts[i+1]*np.ones(2), (0.5,1), 'k')
    
    plt.plot(vid_file_2.ts[vid2_indx[0]]*np.ones(2), (-0.5,-1), 'k')
    plt.plot(vid_file_2.ts[vid2_indx[1]]*np.ones(2), (-0.5,-1), 'k')
    plt.plot(vid_file_2.ts[vid2_indx[2]]*np.ones(2), (-0.5,-1), 'k')
    
    plt.xticks(())
    plt.yticks(())
    plt.xlim((min_ts, max_ts))
    plt.ylim((-1, 1))

    # resize the figure to correct size    
    fig.set_size_inches(FRAME_SZ[0]*3//DPI, FRAME_SZ[1]*2//3//DPI)
    fig.set_dpi(DPI)
    
    fig.canvas.draw()
 
    # Get the RGBA buffer from the figure
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (w, h, 4)
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll(buf, 3, axis=2)
    im_trc = PIL.Image.frombytes("RGBA", (w, h), buf.tobytes())
    res.paste(im_trc, (0, FRAME_SZ[1]))
    
    plt.close('all')

    res.save('%s/frame-%07.f.png' % (OUT_FLDR, i), 'PNG')

  
    
