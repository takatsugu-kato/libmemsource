import setuptools

setuptools.setup(
    name="libmemsource",
    version="1.4.9",
    author="tkato",
    author_email="kato@ideainstitute.co.jp",
    description="libmemsource module handles memsource.",
    long_description="libmemsource module handles memsource.",
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7.3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'retry',
        'urllib3',
        'lxml'
    ]
)
