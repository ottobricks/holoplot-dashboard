# DataOps Engineer case
### Applicant - Otto von Sperling

## Task Guidelines
HOLOPLOT is at the beginning of the manufacturing process of new Pro Audio devices. Having
recently launched the ORION series, the company is striving to ramp up production.
The manufacturing of the components is done externally, but the final assembly and Quality
Assurance is taking place in Berlin. The QA process is supported by various measurement
tools that are used at different stages throughout the process.
During the QA process for the incoming loudspeakers we test them with a tool called CLIO.
This testing outputs the analysis results of each speaker test in a set of data files. You
can find a collection of these files in the Data folder.

The files looks like this, with added information in parenthesis:

    1 GOOD SIN                  (this is the overall test result of the speaker)
        Response GOOD           (this is the result of the response sub-test)
        Polarity GOOD           (this is the result of the polarity sub-test)
        RUB+BUZZ GOOD           (this is the result of the rub and buzz sub-test)
        THD GOOD                (this is the result of the total harmonic distortion sub-test)
    15.10.2018 11.59.51         (the precise timestamp of the test)
    UNIT N. F090-00575 GOOD     (the speaker serial number and overall result, again)

It is your task to analyze the given files and then create a dashboard or tool that allows
us to visualize the results. The minimum of features this tool needs to provide are:
* Allow the user to choose a date and show all speakers with their 5 results
(overall, response, polarity, rub+buzz, thd)
* Allow the user to specify a specific serial number and show the 5 results (overall,
response, polarity, rub+buzz, thd) for that speaker
* Show a summary of number of good speakers, number of bad speakers, the average
failure rate and the standard deviation of the failure rate for a given date range.
* Provide an additional set of data files and process them.


Please provide ample information on how you set up the tool and how we can best evaluate
your solution.

## Solution Overview
This dashboard contains three main widgets:

1. A multi selection box to pick the category of overall results within a given date range, and its accompanying chart;
2. A file uploader box into which multiple files can be dragged and dropped, or picked with the O.S. file manager (not tested on windows yet);
3. A multi selection box to pick specific devices based on their serial number. Their results are displayed in a table (full set of features) and an accompanying polar chart. Results are also displayed if an element is clicked in the chart

![alt text](https://github.com/ottok92/holoplot-dashboard/blob/master/assets/Screenshot%20from%202019-07-30%2011-46-31.png?raw=true "Logo Title Text 1")

## Challenges in development
These were the 3 major pain points in the development of this dashboard:
1. Parsing the data, fixing errors and handling exceptions;
2. Developing an infrastructure for multi-user case;
3. Working with a new set of tooling for the first time;

### 1. The Data
This was a rather interesting task. Upfront, it seemed like the dataset was quite simple, with few 'columns' and single-level index dependency. Nevertheless, further exploration brought out some holes in the dataset.

First, the fact that some files had irregular or missing entries (e.g., 'Response go od') made it necessary to dig deeper and implement custom parsing methods to handle such exceptions.
For instance, the method `def parse_test_results(fname: str) -> list` handles the following cases while reading the input files:

1. the overall result is missing but the other 4 results are present, it infers the overall result;
2. any of the 4 results is missing but the overall is present, it infers the missing features;
3. the serial number is missing, fetches it from the file name;

A number of other methods have been implemented to catch exceptions and handle them. Due to the time constraint, they have been shallowly documented. Intuitive naming conventions are of help, though.

### 2. The Infrastructure
It's easy to forget that we do not implement systems to be used only by us. Writing code that is not parallelizable is a trap that many fall into. And honestly, it wasn't until half-way through the implementation that I realized my design had this flaw. No worries, the challenge got me even more interested in finding a solution. For that, there were a few priorities I wanted to keep in check. No proprietary software, no resource hungry frameworks and no cloud-based solutions could be used. HA! That sounds like a party. Before I comment on how I went about making my code parallelizable, let me get briefly into the tooling.

So Django was out of the game, in favor of pure-Python+Flask. I did consider going for that good old C stack, but honestly I was a bit too rusty to get it done in one week. Also, keep in mind that Cython can give Python some of that good C power under the hood. Now, charts. Matplotlib or Plotly? I went with Plotly due to more interactive plots with less code (not to say that it's easier, though). For the front-end, I decided to try out a Python module that I've had an eye on for a while, Dash by Plotly (what a coincidence!). One might say that Dash is a parser of Python into the MVC stack, with the added benefit of having Plotly bundled with it. And that's it. I got the tooling, the editor (VSCode and Vim), the challenge and a tight schedule with the upcoming end-of-semester craze at the university. Nothing that good coffee and good music can't carry along.

Now, back to the elephant in the room. How can I make this dashboard run for multiple users without the actions of one interfering with others? The solution I proposed here was to do the expensive computation on the dataset once, keep it in the browser (aka. let the operating system handle it in the RAM or Cache) and share it as a preprocessed json whenever a widget requested it. Is this the best way to do it? No, it is not because it's not too scalable. But it is perfect for the application at hand and the ease of setting up once it's done. No need for shared or complex filesystems. You pretty much install the dependencies (which are not many) and you are good to go.

### 3. The Tooling
It will be quite apparent that working with front-end development is not yet an expertise of mine. Having said that, this project has been a great opportunity to brush up on my CSS and fight a bit with JS. In the end, Dash helped a lot by bringing the MVC stack a bit closer to what I am used to, while being challenging enough to keep one's interest. That's the right recipe for growing! In future versions, it would be necessary to modularize the code and get rid of those inline CSS monsters.


## How to run it:
Really, it's all too simple if you rock a Linux machine. If it's your first time running:
    
    cd ~/path-where-to-install-dashboard/
    git clone https://github.com/ottok92/holoplot-dashboard.git orion_dashboard
    bash orion_dashboard/run.sh
    
But if you've already got the dashboard on your machine, just run:
    
    bash ~/path-to-dashboard/orion_dashboard/run.sh
    
Voilà, your browser will be started on the dashboard page (you might have to hit reload just to tell it to wake up) and you are set to take a look at how those nice Orion speakers are doing! Be sure to upload new files to keep yourself up to date (they will be stored for you so that you don't need to upload them again :grin:)

Regarding Windows, it seems things aren't as easy. I should be posting soon how to go about it.

## How to kill it:
Go back to the terminal where you ran 'bash ./run.sh' and press the combination of keys <Ctr+c> to kill the running dashboard
