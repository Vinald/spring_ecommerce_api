<template>
  <div class="container">
    <div class="text-center mt-4">
      Please note that statistics on this
      dashboard are refreshed every after 2 seconds
    </div>
    <hr />
    <div class="row mt-4">
      <div class="col-md-3">
        <div class="usage-monitor mb-3">
          <div>Server Up Time</div>
          <div class="text-primary">{{ serverUpTime }}</div>
        </div>
        <div class="usage-monitor mb-3">
          <div>
            SIP Trunk Channel Usage
            <span class="badge badge-secondary">{{ activeCalls }}/{{ maxSIPChannels }}</span>
          </div>
          <b-progress
            :value="activeCalls"
            :max="maxSIPChannels"
            height="5px"
            :variant="variant(activeCalls/maxSIPChannels*100)"
          ></b-progress>
        </div>
        <div class="usage-monitor mb-3">
          <div>CPU Usage <span class="badge badge-secondary">{{ cpuUsage }}%</span></div>
          <b-progress :value="cpuUsage" :variant="variant(cpuUsage)" :max="100" height="5px"></b-progress>
        </div>
        <div class="usage-monitor mb-3">
          <div>Memory Usage <span class="badge badge-secondary">{{ memoryUsage }}%</span></div>
          <b-progress :value="memoryUsage" :variant="variant(memoryUsage)" :max="100" height="5px"></b-progress>
        </div>
        <div class="usage-monitor mb-3">
          <div>Disk Usage <span class="badge badge-secondary">{{ diskUsage }}%</span></div>
          <b-progress :value="diskUsage" :variant="variant(diskUsage)" :max="100" height="5px"></b-progress>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="text-success fas fa-phone-volume fa-4x"></i>
            <h3 class="card-title mt-4">Active Calls</h3>
            <h4 class="card-title mt-4 text-success">{{ activeCalls }}</h4>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="text-info fas fa-phone-alt fa-4x"></i>
            <h3 class="card-title mt-4">Queued Calls</h3>
            <h4 class="card-title mt-4 text-info">{{ queuedCalls }}</h4>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="text-secondary fas fa-phone-slash fa-4x"></i>
            <h3 class="card-title mt-4">Processed Calls</h3>
            <h4 class="card-title mt-4 text-secondary">{{ processedCalls }}</h4>
          </div>
        </div>
      </div>
    </div>
    <div class="row mt-4">
      <div class="col-md-3">
        <div class="custom-card">
          <h5 class="text-center">Asterisk</h5>
          <hr />
          <div>Status:
            <span v-if="asteriskUpTime !== 'n/a'" class="text-success float-right">Active (Online)</span>
            <span v-else class="text-danger float-right">Offline</span>
          </div>
          <div>Up time: <span class="text-primary float-right">{{ asteriskUpTime }}</span></div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="custom-card">
          <h5 class="text-center">IVR API</h5>
          <hr />
          <div>Status:
            <span v-if="ivrApiUpTime !== 'n/a'" class="text-success float-right">Active (Online)</span>
            <span v-else class="text-danger float-right">Offline</span>
          </div>
          <div>Up time: <span class="text-primary float-right">{{ ivrApiUpTime }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Home',
  data() {
    return {
      cpuUsage: 0,
      diskUsage: 0,
      memoryUsage: 0,
      activeCalls: 0,
      queuedCalls: 0,
      maxSIPChannels: 0,
      processedCalls: 0,
      serverUpTime: 'n/a',
      asteriskUpTime: 'n/a',
      ivrApiUpTime: 'n/a',
      statsURL: process.env.VUE_APP_ROOT_API,
    };
  },
  mounted() {
    window.setInterval(() => {
      this.stats();
    }, 2000);
  },
  methods: {
    stats() {
      axios.get(`${this.statsURL}/dashboard-stats`).then((response) => {
        this.cpuUsage = response.data.cpu;
        this.diskUsage = response.data.disk;
        this.memoryUsage = response.data.memory;
        this.activeCalls = response.data.channels;
        this.queuedCalls = response.data.queued_calls;
        this.maxSIPChannels = response.data.max_sip_channels;
        this.processedCalls = response.data.processed_calls;
        this.serverUpTime = response.data.server_up_time;
        this.asteriskUpTime = response.data.asterisk_up_time;
        this.ivrApiUpTime = response.data.ivr_api_up_time;
      });
    },
    variant(value) {
      if (value >= 90) {
        return 'danger';
      }
      if (value >= 70) {
        return 'warning';
      }
      if (value >= 50) {
        return 'info';
      }
      if (value > 0) {
        return 'success';
      }
      return '';
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">

</style>
