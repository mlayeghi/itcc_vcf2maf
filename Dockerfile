FROM princessmaximacenter/vcf2maf:1.6.20

RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list \
  && sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list \
  && apt-get update -o Acquire::Check-Valid-Until=false \
  && apt-get install -y wget unzip ca-certificates tar \
  && rm -rf /var/lib/apt/lists/*

# Install OpenJDK 17 (Temurin JRE) manually
RUN wget -O /tmp/jdk17.tar.gz \
    https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10+7/OpenJDK17U-jre_x64_linux_hotspot_17.0.10_7.tar.gz && \
    mkdir -p /opt/java &&  \
    tar -xzf /tmp/jdk17.tar.gz -C /opt/java &&  \
    rm /tmp/jdk17.tar.gz &&  \
    mv /opt/java/jdk-17* /opt/java/jdk17

ENV JAVA_HOME=/opt/java/jdk17
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
    /opt/conda/bin/conda install -y pandas psutil && \
    /opt/conda/bin/conda clean -afy

ENV PATH="/opt/conda/bin:${PATH}"

COPY pedcan_vcf2maf.py /opt/itcc_vcf2maf/
COPY run_vcf2maf.py /opt/itcc_vcf2maf/
COPY run_cnv2seg.py /opt/itcc_vcf2maf/
COPY config_loader.py /opt/itcc_vcf2maf/
COPY config.json /opt/itcc_vcf2maf/
COPY make_cbio_release.sh /opt/itcc_vcf2maf/
COPY scripts /opt/itcc_vcf2maf/scripts
COPY templates /opt/itcc_vcf2maf/templates

ENV PATH="/opt/itcc_vcf2maf/:${PATH}"