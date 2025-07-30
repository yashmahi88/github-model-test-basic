
pipeline {
    agent {
        label 'Yocto'
    }

    environment {
        BASE_PATH = "/mnt/build" 
        NEW_DIR = "myhello"

        YOCTO_WORKSPACE   = "${BASE_PATH}/poky"
        POKY_DIR          = "${YOCTO_WORKSPACE}"
        BUILD_DIR         = "${POKY_DIR}/build"

        SSTATE_DIR_PATH = '/mnt/efs/fs/yocto-sstate'
        DL_DIR_PATH     = '/mnt/efs/fs/yocto-dl'
        TMP_DIR_PATH    = '/mnt/build/tmp'

        MACHINE         = 'qemux86-64'
        IMAGE           = 'core-image-minimal'

        BB_NUMBER_THREADS = '8'
        PARALLEL_MAKE     = '-j4'
    }

    options {
        timeout(time: 4, unit: 'HOURS')
        skipDefaultCheckout()
        timestamps ()
    }

    stages {
        stage('Prepare Yocto Workspace') {
            steps {
                script {
                    echo "Preparing Yocto workspace at ${YOCTO_WORKSPACE}"
                    sh """
                        echo "${YOCTO_WORKSPACE}"
                        sudo chown -R jenkins:jenkins /mnt/build/*
                        sudo chmod 755 /mnt/build/*
                        mkdir -p /mnt/efs/fs/yocto-dl 
                        mkdir -p /mnt/efs/fs/yocto-sstate
                        sudo chown -R jenkins:jenkins /mnt/efs/fs/yocto-dl/
                        sudo chown -R jenkins:jenkins /mnt/efs/fs/yocto-sstate/
                        sudo rm -rf "${BUILD_DIR}"
                    """
                }
            }
        }

        stage('Clone Repositories') {
            steps {
                script {
                    echo "Cloning Poky repository..."

                    dir("${YOCTO_WORKSPACE}") {
                        git branch: 'kirkstone', url: 'https://git.yoctoproject.org/git/poky'
                    } 
                    dir("${BASE_PATH}/${NEW_DIR}") { 
                        echo "Cloning meta-myhello layer..."
                        git branch: 'main', url: 'https://github.com/santoshPagire/yocto_new.git'
                        sh "cp -r meta-myhello/ ../poky"
                    }
                }
            }
        }

        stage('Configure Build Environment') {
            steps {
                script {

                    dir("${YOCTO_WORKSPACE}") {
                        sh '''
                            bash -c '
                                pwd
                                source oe-init-build-env 
                            '
                        '''
                    }
                    sh """
                        echo "# Setting MACHINE" >> ${BUILD_DIR}/conf/local.conf
                        echo 'MACHINE = "${MACHINE}"' >> ${BUILD_DIR}/conf/local.conf

                        echo "# Setting parallel build options" >> ${BUILD_DIR}/conf/local.conf
                        echo 'BB_NUMBER_THREADS = "${BB_NUMBER_THREADS}"' >> ${BUILD_DIR}/conf/local.conf
                        echo 'PARALLEL_MAKE = "${PARALLEL_MAKE}"' >> ${BUILD_DIR}/conf/local.conf

                        echo "# Setting shared state and download directories" >> ${BUILD_DIR}/conf/local.conf
                        echo 'SSTATE_DIR ?= "${SSTATE_DIR_PATH}"' >> ${BUILD_DIR}/conf/local.conf
                        echo 'DL_DIR ?= "${DL_DIR_PATH}"' >> ${BUILD_DIR}/conf/local.conf
                        echo 'TMPDIR = "${TMP_DIR_PATH}"' >> ${BUILD_DIR}/conf/local.conf

                        echo "# Adding custom packages" >> ${BUILD_DIR}/conf/local.conf
                        echo 'CORE_IMAGE_EXTRA_INSTALL += "hello-world"' >> ${BUILD_DIR}/conf/local.conf

                    """
                    sh """
                        echo "# Adding custom layers to bblayers.conf"
                        sed -i '/^BBLAYERS ?= /a \\  /mnt/build/poky/meta-myhello \\\\' /mnt/build/poky/build/conf/bblayers.conf
                    """
                }
            }
        }

        stage('Build Yocto Image') {
    steps {
        script {
            echo "Starting BitBake for image: ${IMAGE}..."
            dir("${YOCTO_WORKSPACE}") {
                sh '''
                    mkdir -p metrics

                    bash -c '
                        pwd
                        source oe-init-build-env 
                        bitbake -c cleansstate perl-native
                        bitbake -c cleansstate openssl
                        bitbake ${IMAGE}
                    ' &
                    BUILD_PID=$!
                    echo "Build PID: $BUILD_PID"
                    # Start psrecord on build PID, logging every 5 seconds
          #          /home/jenkins/.local/bin/psrecord $BUILD_PID --log metrics/yocto_usage.csv --interval 5 --include-children &

                      /home/jenkins/.local/bin/psrecord $BUILD_PID --log - --interval 5 --include-children | awk -v start="$(date +%s)" '
                      BEGIN {
                      print "Timestamp,Elapsed time,CPU (%),Real (MB),Virtual (MB)"
                      }
                      NR > 1 {
                      now = strftime("%Y-%m-%d %H:%M:%S", start + $1)
                      printf "%s,%.3f,%s,%s,%s\n", now, $1, $2, $3, $4
                      }' > metrics/yocto_usage.csv &

                    PSRECORD_PID=$!

                    # Wait for the build to finish
                    wait $BUILD_PID

                    # After build ends, stop psrecord
                    kill $PSRECORD_PID || true

                    echo "Build complete. Metrics saved to metrics/yocto_usage.csv"
                    mv metrics/yocto_usage.csv ${WORKSPACE}/yocto_usage.csv
                '''
            }
        }
    }
}


        // stage('Archive Build Artifacts') {
        //     steps {
        //         script {
        //             echo "Archiving generated images..."
        //             def deployDir = "${BUILD_DIR}/tmp/deploy/images/${MACHINE}"
        //             archiveArtifacts artifacts: "${deployDir}/**", fingerprint: true, allowEmptyArchive: false
        //             echo "Images archived from ${deployDir}"
        //         }
        //     }
        // }
    }

    post {
        always {
            // Archive the CSV
            archiveArtifacts artifacts: 'yocto_usage.csv', fingerprint: true

            // Plot CPU
            plot csvFileName: 'yocto_cpu_plot.csv',
            group: 'Yocto Build Metrics',
            title: 'Yocto CPU Usage',
            style: 'line',
            yaxis: 'CPU (%)',
            csvSeries: [[file: 'yocto_usage.csv', inclusionFlag: 'INCLUDE_BY_COLUMN', url: '', displayTableFlag: false]]

            // Plot Memory
            plot csvFileName: 'yocto_mem_plot.csv',
            group: 'Yocto Build Metrics',
             title: 'Yocto Memory Usage',
             style: 'line',
             yaxis: 'Memory (%)',
             csvSeries: [[file: 'yocto_usage.csv', inclusionFlag: 'INCLUDE_BY_COLUMN', url: '', displayTableFlag: false]]
            cleanWs()
        }
        success {
            echo "Yocto image build SUCCEEDED!"

        }
        failure {
            echo "Yocto image build FAILED!"
        }
        unstable {
            echo "Yocto image build UNSTABLE (e.g., some tests failed)."
        }
    }
}
