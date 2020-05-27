"""Module that caches web requests."""

import requests
from requests import RequestException
import logging
from datetime import datetime

DEFAULT_DURATION = 21600  # 6 hrs in sec


class WebCache:
    """Caches web requests."""

    def __init__(self, duration=DEFAULT_DURATION):
        """Initialize variables."""
        self.data = dict()  # Maps url -> [data, timestamp]
        self.duration = duration

    def get(self, url, function=None, fallback=None):
        """Get the json returned by an url.

        If a 'function' is defined, the result of 'function(json)' gets returned.
        """
        if self.isExpired(url):
            timestamp = datetime.now()
            json = self.loadJSON(url)
            if json:
                if function is not None:
                    result = function(json)
                else:
                    result = json
                self.data[url] = [result, timestamp]
                return result
            else:
                # fallback if url down or json cannot be loaded
                if url in self.data:
                    return self.data[url][0]
                else:
                    if fallback is not None:
                        self.data[url] = [fallback, timestamp]
                        return fallback
                    else:
                        raise RequestException
        else:
            return self.data[url][0]

    def isExpired(self, url):
        """Return whether recent data exists for the given url."""
        if url in self.data:
            return (datetime.now() - self.data[url][1]).seconds > self.duration
        else:
            return True

    def loadJSON(self, url):
        """Load a JSON from an url, return False if something fails."""
        try:
            r = requests.get(url)
            r.raise_for_status()
            return r.json()

        except RequestException as e:
            # Fail to get JSON from URL
            logging.critical("Cannot load url: {}".format(url))
            logging.warning(e)

            return False

        except ValueError as e:
            # Server returned something that can't be parsed as json
            logging.critical("Url ({}), failed to parse JSON.".format(url))
            logging.warning(e)

            return False
