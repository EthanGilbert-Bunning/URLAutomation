# URL Automation Project

## Getting Started
To get started with the URL Automation project, follow these steps:
1. Install required dependencies:
    ```
    $ pip install -r requirements.txt
    ```

2. Run the script:
    ```
    $ python urlautomation.py
    ```

Note that the command is using `urlautomation.py` and NOT `urlautomation`.
If you try to use `python urlautomation`, you will get the following error:
```
This program is not meant to be run as a package.
Please, use the provided urlautomation.py script in the root directory.
```

## Basic usage
Before running the script, make sure you create your own configuration file. This can be
done by copying the `example_config.json` file to `config.json`, like:
   ```
   $ cp example_config.json config.json
   ```

In this config, you will need to provide both the name of the database file, and
your [SecurityTrails](https://securitytrails.com/) API key.

Additionally, you may also specify your own config file, with:
```
$ python urlautomation.py -c my_config.json
```

The script is designed to be run from the command line. You can run the following command to see the available options:
```
$ python urlautomation.py --help
usage: urlautomation.py [-h] [-c CONFIG] {case,domain} ...

URL Automation CLI

positional arguments:
  {case,domain}
    case                Class for handling case commands in the CLI.
    domain              Class for handling domain commands in the CLI.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the configuration file
```

For the command that you're interested in, for example `domain`, you can view the help like this:
```
$ python urlautomation.py domain --help
usage: urlautomation.py domain [-h] {fetch,search,query,list} ...

positional arguments:
  {fetch,search,query,list}
    fetch               Fetch information about a domain
    search              Search for links to a domain
    query               Query information about a domain
    list                List all domains

options:
  -h, --help            show this help message and exit
```
A similar pattern applies for the subcommands, for example:
```
$ python urlautomation.py domain fetch --help
usage: urlautomation.py domain fetch [-h] [--dump] [--simulate] [--quick] name

positional arguments:
  name        Name of the domain to fetch for

options:
  -h, --help  show this help message and exit
  --dump      Dump the results of web requests to JSON files.
  --simulate  Simulate the fetch based on hardcoded responses.
  --quick     Fetch only data that can be gathered from minimal requests (e.g. no extended info for SSL certificates).
```

## Testing functionality with provided dataset
1. Add the test domain data to the database:
```
$ python urlautomation.py domain fetch --simulate game.pokerkg.com gamebusadmin3.zrdqkj.com kgvip.com pokerkg.com pokerkg.dev wwwpoker.sydztc2012.com gamebusadmin3.zrdqkj.com
```
2. Create a new case:
```
$ python urlautomation.py case create Test
```
3. Add the test domains to the case:
```
$ python urlautomation.py case domains add --case Test game.pokerkg.com gamebusadmin3.zrdqkj.com kgvip.com pokerkg.com pokerkg.dev wwwpoker.sydztc2012.com
```
4. Generate a report:
```
$ python urlautomation.py case report --case Test
```
