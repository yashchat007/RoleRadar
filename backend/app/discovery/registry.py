from collections.abc import Callable

from app.discovery.adapters.amazon import AmazonOfficialAdapter
from app.discovery.adapters.bofa import BankOfAmericaOfficialAdapter
from app.discovery.adapters.goldman import GoldmanSachsOfficialAdapter
from app.discovery.adapters.jpmorgan import JPMorganOfficialAdapter
from app.discovery.adapters.morgan_stanley import MorganStanleyOfficialAdapter
from app.discovery.adapters.apple import AppleOfficialAdapter
from app.discovery.adapters.atlassian import AtlassianOfficialAdapter
from app.discovery.adapters.cloudflare import CloudflareOfficialAdapter
from app.discovery.adapters.google import GoogleOfficialAdapter
from app.discovery.adapters.meta import MetaOfficialAdapter
from app.discovery.adapters.microsoft import MicrosoftOfficialAdapter
from app.discovery.adapters.stripe import StripeOfficialAdapter

ADAPTERS: dict[str, Callable[[], object]] = {
    "amazon_official": AmazonOfficialAdapter,
    "apple_official": AppleOfficialAdapter,
    "atlassian_official": AtlassianOfficialAdapter,
    "cloudflare_official": CloudflareOfficialAdapter,
    "bofa_official": BankOfAmericaOfficialAdapter,
    "goldman_official": GoldmanSachsOfficialAdapter,
    "google_official": GoogleOfficialAdapter,
    "jpmorgan_official": JPMorganOfficialAdapter,
    "morgan_stanley_official": MorganStanleyOfficialAdapter,
    "meta_official": MetaOfficialAdapter,
    "microsoft_official": MicrosoftOfficialAdapter,
    "stripe_official": StripeOfficialAdapter,
}


def get_adapter(adapter_key: str):
    factory = ADAPTERS.get(adapter_key)
    if not factory:
        raise KeyError(adapter_key)
    return factory()
