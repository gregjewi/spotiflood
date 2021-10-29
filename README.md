![](https://raw.githubusercontent.com/gregjewi/spotiflood/main/misc/spotiflood.png)

Out of an interest in the interface of science and music, **this project sonifies hydrological data** from Iowa.
This result is a **python-based workflow** where users can produce, play, and save (in wav format) music from 10 years of daily streamflow data of a currated dataset of 32 USGS gages in the Des Moines River Watershed.

**Make music yourself by downloading the repo and using [`spotiflood.ipynb`](https://github.com/gregjewi/spotiflood/blob/main/spotiflood.ipynb)**

Below is a sample "score" to a composition built from streamflow data for one water year from the Raccoon River basin, a major tributary of the Des Moines River.
![](https://raw.githubusercontent.com/gregjewi/spotiflood/main/misc/sampleSong.png)


# Our Process
We began by exploring the data from a variety of flow and water height sensors as data to control the pitch of computer-generated tones in R and Python. 
Considering the harshness of the timbre of computer tones, we focused on fading them in and out by controlling their amplitude. 
We also opted to bin data and associate bins with specific frequencies that correspond to musical notes, increasing the musicality and listenability of the water music. 
We used two distinctive scales -- a double harmonic scale that harkens to Middle Eastern music and a pentatonic scale common in East Asian music -- in addition to a standard chromatic scale used in Western music. 

We found the follow to produce results that have sound with musicality:
- Choose a "dominant" gage; usually a gage that measures the furthest downstream point in a network of streamflows. Data from this gage will provide the dominant sound.
- Choose auxiliary gages for harmonics; usually gages that are nested within the larger basin of the dominant gage
- Choose the tonal system for the flow to frequency mapping. We have three preloaded systems: pentatonic scale, a double harmonic scale, and a chromatic scale.
- Perform the mapping of flows to frequencies. (Optionally calculate waveform amplitudes based on the streamflow data as well.) The output is a sequence of frequency (and/or amplitudes.)
- Use the frequency (and amplitude) data to generate an array of values that can be played like a wav file.
- Play! Listen, iterate, explore.
- Save your creations to `.wav` file.
