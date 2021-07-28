<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4">
        <div class="col-12">
          <div class="text-center" v-if="message">
            <b-alert show dismissible :variant="label">{{ message }}</b-alert>
          </div>
          <h5 class="text-center mb-4">Reports</h5>
          <hr/>
          <div class="justify-content-center">
            <b-button variant="secondary" class="mr-3 shadow" @click="$bvModal.show('create-new-report')">
              <i class="fas fa-plus-circle mr-1"></i> Add
            </b-button>
            <b-button variant="danger" class="mr-3 shadow" v-if="reports.length !== 0" @click="deleteReports()">
              <i class="fas fa-trash-alt mr-1"></i> Delete
            </b-button>
            <b-button variant="primary" class="shadow" v-if="reports.length !== 0" @click="refresh()">
              <i class="fas fa-redo-alt mr-1"></i> Refresh
            </b-button>
            <b-modal id="create-new-report" title="Create Report" hide-footer>
              <form @submit.prevent="createReport">
                <div class="form-group">
                  <b-form-checkbox v-model="isScheduled" name="check-button" switch>Scheduled</b-form-checkbox>
                </div>
                <div class="form-group" v-if="!isScheduled">
                  <label for="date-from">Start Date</label>
                  <input v-model="reportForm.startDate" type="date" class="form-control" id="date-from">
                </div>
                <div class="form-group" v-if="!isScheduled">
                  <label for="date-to">End Date</label>
                  <input v-model="reportForm.endDate" type="date" class="form-control" id="date-to">
                </div>
                <div class="form-group" v-if="isScheduled">
                  <label for="report-name">Report name</label>
                  <input type="text" class="form-control" id="report-name" v-model="reportForm.name">
                </div>
                <div class="form-group">
                  <label>App</label>
                  <b-form-select v-model="reportForm.app" :options="apps"></b-form-select>
                </div>
                <div class="form-group" v-if="isScheduled">
                  <label>Recurrence</label>
                  <b-form-select v-model="reportForm.recurrence" :options="recurrenceOptions"></b-form-select>
                </div>
                <div class="form-group" v-if="isScheduled && reportForm.recurrence === 'weekly'">
                  <label>Day of week</label>
                  <b-form-select v-model="reportForm.day" :options="daysOfWeek"></b-form-select>
                </div>
                <div class="form-group" v-if="isScheduled && reportForm.recurrence !== 'monthly'">
                  <label for="report-time">Time</label>
                  <input type="time" class="form-control" id="report-time" v-model="reportForm.time">
                </div>
                <div class="form-group" v-if="isScheduled">
                  <label>To recipients</label>
                  <b-form-textarea
                    v-model="reportForm.to"
                    placeholder="For example user1@example.com,user2@example.com"
                    rows="3"
                    max-rows="6"
                  >
                  </b-form-textarea>
                </div>
                <div class="form-group" v-if="isScheduled">
                  <label>Cc recipients</label>
                  <b-form-textarea
                    v-model="reportForm.cc"
                    placeholder="For example user1@example.com,user2@example.com"
                    rows="3"
                    max-rows="6"
                  >
                  </b-form-textarea>
                </div>
                <button v-if="creatingReport" class="btn btn-primary float-right">
                  <i class="fas fa-circle-notch fa-spin"></i> Creating report. Please wait...
                </button>
                <div v-else>
                  <button v-if="isScheduled" type="submit" class="btn btn-primary float-right">Schedule Report</button>
                  <button v-else type="submit" class="btn btn-primary float-right">Generate Report</button>
                </div>
              </form>
            </b-modal>
          </div>
          <hr/>
        </div>
      </div>
      <div class="row mt-4">
        <div class="col-8">
          <div class="table-responsive shadow">
            <b-table
              class="text-center"
              head-variant="dark"
              borderless
              hover
              :items="reports"
              :fields="reportFields"
              :busy="isLoadingReports"
            >
              <template v-slot:table-busy>
                <div class="text-center text-danger my-2">
                  <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
                </div>
              </template>
              <template v-slot:cell(#)="data">
                <input type="checkbox" :value="data.item.id" v-model="checkedReports">
              </template>
              <template v-slot:cell(name)="data">
                <a href="#" @click="editReport(data.item)">{{ data.item.name }}</a>
                <b-modal
                  :id="data.item.id + 'edit-report'"
                  :title="'Edit report: ' + editReportForm.name" hide-footer>
                  <form @submit.prevent="updateReport()">
                    <div class="form-group">
                      <label for="edit-report-name">Report name</label>
                      <input type="text" class="form-control" id="edit-report-name" v-model="editReportForm.name">
                    </div>
                    <div class="form-group">
                      <label>App</label>
                      <b-form-select v-model="editReportForm.app" :options="apps"></b-form-select>
                    </div>
                    <div class="form-group">
                      <label>Recurrence</label>
                      <b-form-select v-model="editReportForm.recurrence" :options="recurrenceOptions"></b-form-select>
                    </div>
                    <div class="form-group" v-if="editReportForm.recurrence === 'weekly'">
                      <label>Day of week</label>
                      <b-form-select v-model="editReportForm.day" :options="daysOfWeek"></b-form-select>
                    </div>
                    <div class="form-group" v-if="editReportForm.recurrence !== 'monthly'">
                      <label for="edit-report-time">Time</label>
                      <input type="time" class="form-control" id="edit-report-time" v-model="editReportForm.time">
                    </div>
                    <div class="form-group">
                      <label>To recipients</label>
                      <b-form-textarea
                        v-model="editReportForm.to"
                        placeholder="For example user1@example.com,user2@example.com"
                        rows="3"
                        max-rows="6"
                      >
                      </b-form-textarea>
                    </div>
                    <div class="form-group">
                      <label>Cc recipients</label>
                      <b-form-textarea
                        v-model="editReportForm.cc"
                        placeholder="For example user1@example.com,user2@example.com"
                        rows="3"
                        max-rows="6"
                      >
                      </b-form-textarea>
                    </div>
                    <button type="submit" class="btn btn-primary float-right">Update</button>
                  </form>
                </b-modal>
              </template>
              <template v-slot:cell(recurrence)="data">
                <span style="text-transform: capitalize;">{{ data.item.recurrence }}</span>
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
import qs from 'qs';
import NavBar from '../components/NavBar.vue';

export default {
  name: 'Reports',
  components: {
    NavBar,
  },
  data() {
    return {
      isScheduled: false,
      apps: [],
      url: process.env.VUE_APP_ROOT_API,
      reportForm: {
        startDate: '',
        endDate: '',
        app: 0,
        to: '',
        cc: '',
        day: '',
        name: '',
        time: '',
        month: '',
        recurrence: '',
      },
      editReportForm: {
        id: '',
        to: '',
        cc: '',
        day: '',
        name: '',
        time: '',
        month: '',
        recurrence: '',
        app: 0,
      },
      daysOfWeek: [
        { value: 1, text: 'Monday' },
        { value: 2, text: 'Tuesday' },
        { value: 3, text: 'Wednesday' },
        { value: 4, text: 'Thursday' },
        { value: 5, text: 'Friday' },
        { value: 6, text: 'Saturday' },
        { value: 7, text: 'Sunday' },
      ],
      recurrenceOptions: [
        { value: 'monthly', text: 'Monthly' },
        { value: 'weekly', text: 'Weekly' },
        { value: 'daily', text: 'Daily' },
      ],
      label: null,
      message: null,
      reports: [],
      creatingReport: false,
      isLoadingReports: false,
      reportFields: ['#', 'name', 'recurrence', 'date_created', 'owner'],
      checkedReports: [],
      isAdmin: false,
    };
  },
  created() {
    this.isAdmin = this.$store.getters.isAdmin;
    this.getReports();
  },
  methods: {
    createReport() {
      if (this.isScheduled) {
        this.scheduleReport();
      } else {
        this.downloadReport();
      }
    },
    async scheduleReport() {
      this.creatingReport = true;
      try {
        const response = await axios.post('reports', qs.stringify(this.reportForm));
        this.label = response.data.status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingReport = false;
        this.$bvModal.hide('create-new-report');
        this.initReportForm();
        this.getReports();
      } catch (e) {
        this.creatingReport = false;
        this.label = 'danger';
        this.message = e.toString();
      }
    },
    refresh() {
      this.getReports();
    },
    async getReports() {
      this.isLoadingReports = true;
      try {
        const response = await axios.get('reports');
        this.apps = response.data.apps;
        this.reports = response.data.reports;
        this.isLoadingReports = false;
      } catch (e) {
        this.label = 'danger';
        this.message = e.toString();
      }
    },
    deleteReports() {
      this.isLoadingReports = true;
      axios.delete(
        'reports',
        { params: { reports: this.checkedReports.toString() } },
      ).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.getReports();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReports = false;
      });
    },
    editReport(data) {
      this.editReportForm = data;
      this.$bvModal.show(`${data.id}edit-report`);
    },
    updateReport() {
      this.$bvModal.hide(`${this.editReportForm.id}edit-report`);
      this.isLoadingReports = true;
      axios.put('reports', qs.stringify(this.editReportForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.getReports();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReports = false;
      });
    },
    initReportForm() {
      this.reportForm.name = '';
      this.reportForm.recurrence = '';
      this.reportForm.to = '';
      this.reportForm.cc = '';
      this.reportForm.day = '';
      this.reportForm.app = 0;
      this.reportForm.time = '';
    },
    async downloadReport() {
      this.creatingReport = true;
      try {
        const dates = `startDate=${this.reportForm.startDate}&endDate=${this.reportForm.endDate}`;
        const response = await axios({
          url: `${this.url}/reports?action=download&app=${this.reportForm.app}&${dates}`,
          method: 'GET',
          responseType: 'blob',
        });
        this.creatingReport = false;
        const fileURL = window.URL.createObjectURL(new Blob([response.data]));
        const fileLink = document.createElement('a');
        fileLink.href = fileURL;
        fileLink.setAttribute('download', 'report.csv');
        document.body.appendChild(fileLink);
        fileLink.click();
      } catch (e) {
        this.creatingReport = false;
        this.label = 'danger';
        this.message = e.toString();
      }
    },
  },
};
</script>
