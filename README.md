# DataOps Engineer case
### Applicant - Otto von Sperling

## Overview
This dashboard contains three main widgets:

1. A multi selection box to pick the category of overall results within a given date range, and its accompanying chart;
2. A file uploader box into which multiple files can be dragged and dropped, or picked with the O.S. file manager (not tested on windows yet);
3. A multi selection box to pick specific devices based on their serial number. Their results are displayed in a table (full set of features) and an accompanying polar chart. Results are also displayed if an element is clicked in the chart

## Challenges in development
These were the 3 major pain points in the development of this dashboard:
1. Parsing the data, fixing errors and handling exceptions;
2. Developing an infrastructure for multi-user case;
3. Working with a new set of tooling for the first time;

### 1. The Data
This was a rather interesting task. Upfront, it seemed like the dataset was quite simple, with few 'columns' and single-level index dependency. Nevertheless, further exploration brought out some holes in the dataset.

First, the fact that some files had irregular or missing entries (e.g., 'Response go od') made it necesary to dig deeper and implement custom parsing methods to handle such exceptions.
For instance, the method `def parse_test_results(fname: str) -> list` handles the following cases while reading the input files:

1. the overall result is missing but the other 4 results are present, it infers the overall result;
2. any of the 4 results is missing but the overall is present, it infers the missing features;
3. the serial number is missing, fetches it from the file name;

A number of other mthods have been implemented to catch exceptions and handle them. Due to the time constraint, they have been shallowly doccumented. Intuitive naming conventions are of help, though.

### 2. The Infrastructure
It's easy to forget that we do not implement systems to be used only by us. Writing code that is not parallelizable is a trap that many fall into. And honestly, it wasn't until half-way through the implementation that I realized my design had this flaw. No worries, the challenge got me even more interested in finding a solution. For that, there were a few priorities I wanted to keep in check. No proprietary software, no resource hungry frameworks and no cloud-based solutions could be used. HA! That sounds like a party. Before I comment on how I went about making my code parallelizable, let me get briefly into the tooling.

So Django was out of the game, in favor of pure-Python+Flask. I did consider going for that good old C stack, but homestly I was a bit too rusty to get it done in one week. Also, keep in mind that Cython can give Python some of that good C power under the hood. Now, charts. Matplotlib or Plotly? I went with Plotly due to more interactive plots with less code (not to say that it's easier, though). For the front-end, I decided to try out a Python module that I've had an eye on for a while, Dash by Plotly (what a coincidence!). One might say that Dash is a parser of Python into the MVC stack, with the added benefit of having Plotly bundled with it. And that's it. I got the tooling, the editor (VSCode and Vim), the challenge and a tight schedule with the upcoming end-of-semester craze at the university. Nothing that good coffee and good music can't carry along.

Now, back to the elephant in the room. How can I make this dashboard run for multiple users without the actions of one interfering with others? The solution I proposed here was to do the expensive computation on the dataset once, keep it in the browser (aka. let the operating system handle it in the RAM or Cache) and share it as a preprocessed json whenever a widget requested it. Is this the best way to do it? No, it is not because it's not too scalable. But it is perfect for the application at hand and the ease of setting up once it's done. No need for shared or complex filesystems. You pretty much install the dependencies (which are not many) and you are good to go.

### 3. The Tooling
It will be quite apparent that working with front-end development is not yet an expertise of mine. On the other hand, there is nothing that is not worthless to learn about, and this project has been a great opportunity to brush up on my CSS and fight a bit with js. In the end, Dash helped a lot by bringing the MVC stack a bit closer to what I am used to, while being challenging enough to keep one's interest. That's the right recipe for growing! In future versions, it would be necessary to modularize more the code and get rid of those inline CSS monsters.


## How to run it
Really, it's all too simple if you rock a Linux machine. It's as simple as:
    
    cd ~/path-where-to-install-dashboard/
    git clone https://github.com/ottok92/holoplot-dashboard.git orion_dashboard
    bash orion_dashboard/install.sh
    
Voilà, your browser will be started on the dashboard page (you might have to hit reload just to tell it to wake up) and you are set to take a look at how those nice Orion speakers are doing! Be sure to upload new files to keep yourself up to date (they will be stored for you so that you don't need to upload them again :grin:)

Instructions for Windows will follow briefly
