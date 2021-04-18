# spotiflood

![](https://raw.githubusercontent.com/gregjewi/spotiflood/main/misc/spotiflood.png)

**Try out our project by downloading the repo and using `spotiflood.ipynb`**

Out of an interest in the interface of science and music, our Hackathon project sought to sonify hydrological data in Iowa.  We first explored the data from a variety of flow and water height sensors as data to control the pitch of computer-generated tones in R and Python. Considering the harshness of the timbre of computer tones, we focused on fading them in and out by controlling their amplitude. We also opted to bin data and associate bins with specific frequencies that correspond to musical notes, increasing the musicality and listenability of the water music. 

While making specific musical notes provides some musicality, the spacing between the notes also contributes. We used two distinctive scales--a double harmonic scale that harkens to Middle Eastern music and a pentatonic scale common in East Asian music--in addition to a standard chromatic scale used in Western music. We also adjusted amplitude (volume) of notes based on their frequencies in order to further reduce harshness. 

Finally, we created brief musical representations of one-year periods of flow data from the Des Moines River Basin. We offer audio files of the raw, computer-generated and hydrology data-based “songs”, as well as a Python code used to create the actual audio, and a brief instrumentation of one watershed created in Finale software using the audio file converted into a MIDI. Next steps will be to integrate this into a web interface that automatically limits and bins data provided by users from even more diverse sources.
