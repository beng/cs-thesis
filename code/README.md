### Requirements
This project has only been tested using the following
* python 2.7
* Chrome or firefox (any browser that supports the web audio API and webkit)
* OS X

### Prerequisites
Download the latests, stable version of [Redis](http://redis.io/)

It is HIGHLY recommended that you use a virtual environment for installing any
python libraries, whether they come from PIP or elsewhere.
Virtual Environment Wrapper (http://virtualenvwrapper.readthedocs.org/en/latest/)
is the preferred choice. Virtual Environment (http://www.virtualenv.org/en/latest/)
is also fine, but requires a separate sandbox for each project.

### Install
`pip -Ur requirements.txt`

### Running
Make sure you run `redis-server` from the project directory since it uses
the redis db dump, `dump.rdb`

`python runserver.py`
