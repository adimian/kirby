from distutils.core import setup

setup(
    name="forecast_to_production",
    version="0.0.1",
    author="Kirby Team",
    license="MIT",
    packages=["forecast_to_production"],
    install_requires=["kirby==0.0.1.dev374", "example_utils"],
)
