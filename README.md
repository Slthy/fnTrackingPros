# fnTracking

User-friendly CLI tool to retrive, store and elaborate data regarding Fortnite™️ proplayers from all over the world!

#### [fnTrackingPros is also on Twitter!](https://twitter.com/fntrackingpros)

## Getting Started

### Requirements

  - A valid TRackerNetwork (TRN) Developer API key
  - Python 3.9.6 or higher.
  - MongoDB Compass is highly recommended


### Installing

- At the first start, use setup wizard `setup.py` to create the `.env` with all your infos.

### Executing program

- After the first run, use `python run.py` CLI, further explanations in `run.py -h`


## Help

If you need to revert any changes to the database, use helper's CLI calling `helper.py`, following the instructions given with `helper.py -h`


## Version History

* 1.2
  * Refactoring update:
    * Bug Fixes
    * Now the tracker can handle the case where a player goes below the top50 and when a player enters in the top50 for the first time  (see `fixUnderTop50` method in `\models.py`)
* 1.1
  * Bug Fixes
* 1.0 - 1.0a
  * Various bug fixes and optimizations
  * Quality-of-Life update: `setup.py`, `run.py` and `helper.py`
  * CLI with documentation
* B0.1
  * Implementation of the core functionalities of the project
* A0.1
  * Initial Release

## TODO - feel free to make pull requests

### Future updates - asap:
  * Unit testing on all the project
  * Better CLI arguments
  * Possible tweet automation

### Next competitive season updates:
  * Full release (version 2.0)
  * Enhanced data storage
  * New statistics
  * Possible player records increase, up to top100


## License

This project is licensed under the 'Creative Commons Legal Code' License - see the LICENSE.md file for details

## Acknowledgments

* [Sometimes I also post on my personal Twitter account](https://twitter.com/aborsato_)
* [Tracker Network](https://tracker.gg)
