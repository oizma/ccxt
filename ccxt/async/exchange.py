# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2017 Igor Kroitor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

#------------------------------------------------------------------------------

import aiohttp
import asyncio
import base64
import calendar
import collections
import datetime
import hashlib
import json
import math
import re
import socket
import ssl
import sys
import time

#------------------------------------------------------------------------------

from ccxt.version import __version__

#------------------------------------------------------------------------------

from ccxt.errors import * # noqa: F403
from ccxt.exchange import Exchange as BaseExchange

#------------------------------------------------------------------------------

__all__ = [
    'Exchange',
]

#------------------------------------------------------------------------------

class Exchange (BaseExchange):

    def __init__(self, config={}):
        super(Exchange, self).__init__(config)
        self.asyncio_loop = self.asyncio_loop or asyncio.get_event_loop()
        self.aiohttp_session = self.aiohttp_session or aiohttp.ClientSession(loop=self.asyncio_loop)

    async def fetch(self, url, method='GET', headers=None, body=None):
        """Perform a HTTP request and return decoded JSON data"""
        headers = headers or {}
        if self.userAgent:
            if type(self.userAgent) is str:
                headers.update({'User-Agent': self.userAgent})
            elif (type(self.userAgent) is dict) and ('User-Agent' in self.userAgent):
                headers.update(self.userAgent)
        if len(self.proxy):
            headers.update({'Origin': '*'})
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        url = self.proxy + url
        if self.verbose:
            print(url, method, url, "\nRequest:", headers, body)
        if body:
            body = body.encode()
        session_method = getattr(self.aiohttp_session, method.lower())
        async with session_method(url, data=body or None, headers=headers, timeout=(self.timeout / 1000)) as response:
            text = await response.text()
            error = None
            details = text if text else None
            if response.status == 429:
                error = ccxt.DDoSProtection
            elif response.status in [404, 409, 500, 501, 502, 521, 525]:
                details = str(response.status) + ' ' + text
                error = ccxt.ExchangeNotAvailable
            elif response.status in [400, 403, 405, 503]:
                # special case to detect ddos protection
                reason = text
                ddos_protection = re.search('(cloudflare|incapsula)', reason, flags=re.IGNORECASE)
                if ddos_protection:
                    error = ccxt.DDoSProtection
                else:
                    error = ccxt.ExchangeNotAvailable
                    details = '(possible reasons: ' + ', '.join([
                        'invalid API keys',
                        'bad or old nonce',
                        'exchange is down or offline',
                        'on maintenance',
                        'DDoS protection',
                        'rate-limiting',
                        reason,
                    ]) + ')'
            elif response.status in [408, 504]:
                error = ccxt.RequestTimeout
            elif response.status in [401, 422, 511]:
                error = ccxt.AuthenticationError
            if error:
                self.raise_error(error, url, method, str(response.status), details)
        if self.verbose:
            print(method, url, "\nResponse:", headers, text)
        return self.handle_response(url, method, headers, text)

    async def load_markets(self, reload=False):
        if not reload:
            if self.markets:
                if not self.markets_by_id:
                    return self.set_markets(self.markets)
                return self.markets
        markets = await self.fetch_markets()
        return self.set_markets(markets)

    async def loadMarkets(self, reload=False):
        return await self.load_markets()

    async def fetch_markets(self):
        return self.markets

    async def fetchMarkets(self):
        return await self.fetch_markets()

    async def fetch_tickers(self):
        raise ExchangeError(self.id + ' API does not allow to fetch all tickers at once with a single call to fetch_tickers () for now')

    async def fetchTickers(self):
        return await self.fetch_tickers()

    async def fetchBalance(self):
        return await self.fetch_balance()

    async def fetchOrderBook(self, market):
        return await self.fetch_order_book(market)

    async def fetchTicker(self, market):
        return await self.fetch_ticker(market)

    async def fetchTrades(self, market):
        return await self.fetch_trades(market)

    async def create_limit_buy_order(self, market, amount, price, params={}):
        return await self.create_order(market, 'limit', 'buy', amount, price, params)

    async def create_limit_sell_order(self, market, amount, price, params={}):
        return await self.create_order(market, 'limit', 'sell', amount, price, params)

    async def create_market_buy_order(self, market, amount, params={}):
        return await self.create_order(market, 'market', 'buy', amount, None, params)

    async def create_market_sell_order(self, market, amount, params={}):
        return await self.create_order(market, 'market', 'sell', amount, None, params)

    async def createLimitBuyOrder(self, market, amount, price, params={}):
        return await self.create_limit_buy_order(market, amount, price, params)

    async def createLimitSellOrder(self, market, amount, price, params={}):
        return await self.create_limit_sell_order(market, amount, price, params)

    async def createMarketBuyOrder(self, market, amount, params={}):
        return await self.create_market_buy_order(market, amount, params)

    async def createMarketSellOrder(self, market, amount, params={}):
        return await self.create_market_sell_order(market, amount, params)

#==============================================================================
