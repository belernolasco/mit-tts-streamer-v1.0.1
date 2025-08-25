from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mit-tts-streamer",
    version="0.1.0",
    author="Beler Nolasco Almonte",
    author_email="beler.nolasco@example.com",
    description="Servidor TTS streaming de baja latencia para sistemas conversacionales de voz en tiempo real",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/mit-tts-streamer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "production": [
            "gunicorn>=21.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mit-tts-streamer=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json", "examples/*"],
    },
)