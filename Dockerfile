FROM princessmaximacenter/vcf2maf:1.6.20

RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
  && sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list \
  && apt-get update -o Acquire::Check-Valid-Until=false \
  && apt-get install -y wget openjdk-11-jre-headless unzip \
  && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"

ARG GATK_VERSION=4.6.1.0
ENV GATK_VERSION=${GATK_VERSION}
RUN wget https://github.com/broadinstitute/gatk/releases/download/${GATK_VERSION}/gatk-${GATK_VERSION}.zip && \
    unzip gatk-${GATK_VERSION}.zip -d /opt/ && \
    rm gatk-${GATK_VERSION}.zip

ENV PATH="/opt/gatk-${GATK_VERSION}:${PATH}"

# Install Miniconda
ENV MINICONDA_VERSION=py312_25.9.1-1
RUN curl -sL https://repo.anaconda.com/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh -o miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    /opt/conda/bin/conda install -y pandas && \
    /opt/conda/bin/conda clean -afy

ENV PATH="/opt/conda/bin:${PATH}"

COPY pedcan_vcf2maf.py /opt/itcc_vcf2maf/
COPY config_loader.py /opt/itcc_vcf2maf/
COPY config.json /opt/itcc_vcf2maf/
COPY scripts /opt/itcc_vcf2maf/scripts

ENV PATH="/opt/itcc_vcf2maf/:${PATH}"