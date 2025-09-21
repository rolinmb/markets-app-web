from consts import FEDFUNDS
import math
from scipy.stats import norm
from scipy.optimize import brentq

class OptionContract:
    def __init__(self, ticker, underlyingprice, strike, yte, lastprice, bidprice, askprice, vol, oi, cp_flag):
        self.underlying = ticker
        self.underlying_price = float(underlyingprice)
        self.strike = float(strike.replace(",", ""))
        self.yte = float(yte)
        self.lastprice = float(lastprice.replace(",", ""))
        self.bidprice = float(bidprice.replace(",", ""))
        self.askprice = float(askprice.replace(",", ""))
        self.midprice = float((self.bidprice + self.askprice) / 2)
        self.volume = float(vol.replace(",", ""))
        self.openinterest = float(oi.replace(",", ""))
        self.iscall = cp_flag
        self.iv = 0.0
        if self.iscall:
            self.iv = implied_volatility_call(self.midprice, self.underlying_price, self.strike, self.yte)
        else:
            self.iv = implied_volatility_put(self.midprice, self.underlying_price, self.strike, self.yte)

    def __repr__(self):
        return (
            f"OptionContract("
            f"underlying='{self.underlying}', "
            f"strike={self.strike}, "
            f"type='{"Call" if self.iscall else "Put"}', "
            f"midprice={self.midprice}, "
            f"yte={self.yte:.4f})"
        )


class OptionExpiry:
    def __init__(self, ticker, date, yte, calls=None, puts=None):
        self.underlying = ticker
        self.date = date
        self.yte = yte
        self.calls = calls if calls is not None else []
        self.puts = puts if puts is not None else []

    def __repr__(self):
        return (
            f"OptionExpiry("
            f"underlying='{self.underlying}', "
            f"date='{self.date}', "
            f"yte={self.yte:.4f}, "
            f"calls={len(self.calls)} contracts, "
            f"puts={len(self.puts)} contracts)"
        )

class OptionChain:
    def __init__(self, ticker, expiries=None):
        self.underlying = ticker
        self.expiries = expiries if expiries is not None else []

    def __repr__(self):
        expiry_dates = [exp.date for exp in self.expiries]
        return (
            f"OptionChain(underlying='{self.underlying}', "
            f"expiries={len(self.expiries)}, "
            f"dates={expiry_dates})"
        )

def bs_call_price(S, K, T, sigma, r=FEDFUNDS):
    if sigma == 0 or T == 0:
        return max(0.0, S - K)
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm.cdf(d1) - K * math.exp(-r*T) * norm.cdf(d2)

def implied_volatility_call(C_market, S, K, T, r=FEDFUNDS):
    # Define function whose root is the implied volatility
    f = lambda sigma: bs_call_price(S, K, T, r, sigma) - C_market
    # Use Brent’s method to find root (sigma)
    try:
        iv = brentq(f, 1e-6, 5)  # volatility between 0.000001 and 500%
    except Exception:
        iv = 0.000001
    return iv

def bs_put_price(S, K, T, sigma, r=FEDFUNDS):
    if sigma == 0 or T == 0:
        return max(0.0, K - S)
    d1 = (math.log(S/K) + (r + 0.5*sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def implied_volatility_put(P_market, S, K, T, r=FEDFUNDS):
    f = lambda sigma: bs_put_price(S, K, T, r, sigma) - P_market
    try:
        iv = brentq(f, 1e-6, 5)  # volatility between 0.0001% and 500%
    except Exception:
        iv = None
    return iv