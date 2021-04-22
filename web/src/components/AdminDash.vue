<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="text-center mt-4">
        Please note that statistics on this
        dashboard are refreshed every after 2 seconds
      </div>
      <div class="row mt-4 mb-4">
        <div class="col-12">
          <div class="responsive shadow">
            <div v-if="isChartLoading" class="text-center">
              <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
            </div>
            <line-chart v-else :download="{background: '#fff'}" :data="chartData"></line-chart>
          </div>
        </div>
      </div>
      <hr>
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
          <div class="card mb-4 shadow">
            <div class="card-body text-center">
              <i class="text-success fas fa-phone-volume fa-4x"></i>
              <h3 class="card-title mt-4">Active Calls</h3>
              <h4 class="card-title mt-4 text-success">{{ activeCalls }}</h4>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card mb-4 shadow">
            <div class="card-body text-center">
              <i class="text-info fas fa-phone-alt fa-4x"></i>
              <h3 class="card-title mt-4">Queued Calls</h3>
              <h4 class="card-title mt-4 text-info">{{ queuedCalls }}</h4>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-4">
          <div class="card shadow">
            <div class="card-body text-center">
              <i class="text-secondary fas fa-phone-slash fa-4x"></i>
              <h3 class="card-title mt-4">Processed Calls</h3>
              <h4 class="card-title mt-4 text-secondary">{{ processedCalls }}</h4>
            </div>
          </div>
        </div>
      </div>
      <div class="row mt-4">
        <div class="col-md-3 mb-4">
          <div class="custom-card shadow">
            <h5 class="text-center">Asterisk</h5>
            <hr />
            <div>Status:
              <span v-if="asteriskUpTime !== 'n/a'" class="text-success float-right">Active (Online)</span>
              <span v-else class="text-danger float-right">Offline</span>
            </div>
            <div>Up time: <span class="text-primary float-right">{{ asteriskUpTime }}</span></div>
          </div>
        </div>
        <div class="col-md-9 mb-4">
            <h5 class="text-center">Asterisk Peers (SIP Trunks)</h5>
          <div class="table-responsive shadow">
            <b-table outlined hover :items="peers" head-variant="dark" :fields="peerFields">
              <template v-slot:cell(host)="data">
                <div class="text-primary">{{ data.item.host }}</div>
              </template>
              <template v-slot:cell(status)="data">
                <div v-if="data.item.status === 'online'" class="text-success">Online</div>
                <div v-else class="text-danger">Offline</div>
              </template>
            </b-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import NavBar from './NavBar.vue';

export default {
  name: 'Home',
  components: {
    NavBar,
  },
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
      peers: [],
      peerFields: [
        { key: 'peer', label: 'Peer name' },
        'host',
        { key: 'max-channels', label: 'Max Channels' },
        { key: 'caller-id', label: 'Caller ID' },
        'status',
      ],
      statsURL: process.env.VUE_APP_ROOT_API,
      chartData: [],
      isChartLoading: false,
    };
  },
  created() {
    this.fetchChartData();
    setInterval(this.stats, 2000);
  },
  methods: {
    async stats() {
      try {
        const response = await axios.get('dashboard-stats');
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
        this.peers = response.data.peers;
      } catch (e) {
        // eslint-disable-next-line no-console
        console.log(e);
      }
    },
    fetchChartData() {
      this.isChartLoading = true;
      axios.get('charts').then((response) => {
        this.isChartLoading = false;
        this.chartData = response.data;
      }).catch((error) => {
        this.isChartLoading = true;
        // eslint-disable-next-line no-console
        console.log(error);
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
