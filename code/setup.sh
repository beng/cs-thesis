# # download and install redis
cd ./bin/
wget http://download.redis.io/releases/redis-2.8.2.tar.gz
tar xzf redis-2.8.2.tar.gz
cd redis-2.8.2
make
cd ../
cp redis.conf ./redis-2.8.2
rm -rf redis-2.8.2.tar.gz
cd ../

# setup virtual environment and install third party libraries
sudo pip install virtualenv
VPATH=`dirname $0`/virtual
mkdir -p $VPATH
virtualenv --distribute --python=`which python2.7` $VPATH
source $VPATH/bin/activate
pip install -Ur requirements.txt
