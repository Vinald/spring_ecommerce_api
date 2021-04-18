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
            <b-button
              variant="primary"
              class="mr-3 shadow"
              v-if="reports.length !== 0 && checkedReports.length <= 1"
              @click="downloadReport()"
            >
              <i class="fas fa-cloud-download-alt mr-1"></i> Download
            </b-button>
            <b-button variant="danger" class="mr-3 shadow" v-if="reports.length !== 0" @click="deleteReports()">
              <i class="fas fa-trash-alt mr-1"></i> Delete
            </b-button>
            <b-button variant="info" class="shadow" v-if="reports.length !== 0" @click="refresh()">
              <i class="fas fa-redo-alt mr-1"></i> Refresh
            </b-button>
            <b-button
              variant="primary"
              class="float-right shadow"
              v-if="isAdmin"
              @click="$bvModal.show('create-report-type')"
            >
              <i class="fas fa-chart-pie mr-1"></i> Create a new report type
            </b-button>
            <b-modal id="create-new-report" title="Create a new report" hide-footer>
              <form @submit.prevent="createNewReport()">
                <div class="form-group">
                  <label for="report-name">Report name</label>
                  <input type="text" class="form-control" id="report-name" v-model="reportForm.name">
                </div>
                <div class="form-group">
                  <label>Report type</label>
                  <b-form-select v-model="reportForm.type" :options="reportTypeOptions()"></b-form-select>
                </div>
                <div class="form-group">
                  <b-form-checkbox id="scheduled" v-model="reportForm.scheduled">Scheduled report</b-form-checkbox>
                </div>
                <div class="form-group" v-if="reportForm.scheduled">
                  <label>Recurrence</label>
                  <b-form-select v-model="reportForm.recurrence" :options="recurrenceOptions"></b-form-select>
                </div>
                <div class="form-group" v-if="reportForm.scheduled && reportForm.recurrence === 'weekly'">
                  <label>Day of week</label>
                  <b-form-select v-model="reportForm.day" :options="daysOfWeek"></b-form-select>
                </div>
                <div class="form-group" v-if="reportForm.scheduled && reportForm.recurrence !== 'monthly'">
                  <label for="report-time">Time</label>
                  <input type="time" class="form-control" id="report-time" v-model="reportForm.time">
                </div>
                <div class="form-group" v-if="reportForm.scheduled">
                  <label>To recipients</label>
                  <b-form-textarea
                    v-model="reportForm.to"
                    placeholder="For example user1@example.com,user2@example.com"
                    rows="3"
                    max-rows="6"
                  >
                  </b-form-textarea>
                </div>
                <div class="form-group" v-if="reportForm.scheduled">
                  <label>Cc recipients</label>
                  <b-form-textarea
                    v-model="reportForm.cc"
                    placeholder="For example user1@example.com,user2@example.com"
                    rows="3"
                    max-rows="6"
                  >
                  </b-form-textarea>
                </div>
                <b-button v-if="creatingReport" variant="primary" class="float-right">
                  <i class="fas fa-circle-notch fa-spin text-primary"></i> Creating report...
                </b-button>
                <button type="submit" class="btn btn-primary float-right">Save</button>
              </form>
            </b-modal>
            <b-modal v-if="isAdmin" id="create-report-type" title="Create new report type" hide-footer>
              <form @submit.prevent="createNewReportType()">
                <div class="form-group">
                  <label for="report-type-name">Report type name</label>
                  <input type="text" class="form-control" id="report-type-name" v-model="reportTypeForm.name">
                </div>
                <div class="form-group">
                  <label>SQL</label>
                  <b-form-textarea
                    id="report-type-sql"
                    v-model="reportTypeForm.sql"
                    placeholder="Enter SQL used to formulate the report"
                    rows="6"
                    max-rows="20"
                  >
                  </b-form-textarea>
                </div>
                <b-button v-if="creatingReportType" variant="primary" class="float-right">
                  <i class="fas fa-circle-notch fa-spin text-primary"></i> Creating report type...
                </b-button>
                <button type="submit" class="btn btn-primary float-right">Save</button>
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
                      <label>Report type</label>
                      <b-form-select v-model="editReportForm.type" :options="reportTypeOptions()"></b-form-select>
                    </div>
                    <div class="form-group">
                      <b-form-checkbox id="scheduled" v-model="editReportForm.scheduled">
                        Scheduled report
                      </b-form-checkbox>
                    </div>
                    <div class="form-group" v-if="editReportForm.scheduled">
                      <label>Recurrence</label>
                      <b-form-select v-model="editReportForm.recurrence" :options="recurrenceOptions"></b-form-select>
                    </div>
                    <div class="form-group" v-if="editReportForm.scheduled && editReportForm.recurrence === 'weekly'">
                      <label>Day of week</label>
                      <b-form-select v-model="editReportForm.day" :options="daysOfWeek"></b-form-select>
                    </div>
                    <div class="form-group" v-if="editReportForm.scheduled && editReportForm.recurrence !== 'monthly'">
                      <label for="edit-report-time">Time</label>
                      <input type="time" class="form-control" id="edit-report-time" v-model="editReportForm.time">
                    </div>
                    <div class="form-group" v-if="editReportForm.scheduled">
                      <label>To recipients</label>
                      <b-form-textarea
                        v-model="editReportForm.to"
                        placeholder="For example user1@example.com,user2@example.com"
                        rows="3"
                        max-rows="6"
                      >
                      </b-form-textarea>
                    </div>
                    <div class="form-group" v-if="editReportForm.scheduled">
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
        <div class="col-4 text-center" v-if="isAdmin">
          <h6 class="mb-4">Report Types</h6>
          <div class="table-responsive shadow">
            <b-table
              head-variant="dark"
              bordered
              hover
              small
              :items="reportTypes"
              :fields="reportTypeFields"
              :busy="isLoadingReportTypes"
            >
              <template v-slot:table-busy>
                <div class="text-center text-danger my-2">
                  <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
                </div>
              </template>
              <template v-slot:cell(name)="data">
                <a href="#" @click="editReportType(data.item)">{{ data.item.name }}</a>
                <b-modal
                  :id="data.item.id + 'edit-report-type'"
                  :title="'Update report type: ' + editReportTypeForm.name" hide-footer>
                  <form @submit.prevent="updateReportType()">
                    <div class="form-group">
                      <label for="edit-report-type-name">Report type name</label>
                      <input
                        type="text"
                        class="form-control"
                        id="edit-report-type-name"
                        v-model="editReportTypeForm.name"
                      >
                    </div>
                    <div class="form-group">
                      <label>SQL</label>
                      <b-form-textarea
                        id="report-type-sql"
                        v-model="editReportTypeForm.sql"
                        placeholder="Enter SQL used to formulate the report"
                        rows="6"
                        max-rows="20"
                      >
                      </b-form-textarea>
                    </div>
                    <button type="submit" class="btn btn-primary float-right">Update</button>
                  </form>
                </b-modal>
              </template>
              <template v-slot:cell(action)="data">
                <a href="#" @click="deleteReportType(data.item.id)" variant="danger">
                  <i class="fas fa-trash text-danger"></i>
                </a>
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
      url: process.env.VUE_APP_ROOT_API,
      reportForm: {
        to: '',
        cc: '',
        day: '',
        name: '',
        type: '',
        time: '',
        month: '',
        recurrence: '',
        scheduled: false,
      },
      editReportForm: {
        id: '',
        to: '',
        cc: '',
        day: '',
        name: '',
        type: '',
        time: '',
        month: '',
        recurrence: '',
        scheduled: false,
      },
      reportTypeForm: {
        sql: '',
        name: '',
      },
      editReportTypeForm: {
        sql: '',
        name: '',
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
      reportTypes: [],
      creatingReport: false,
      creatingReportType: false,
      isLoadingReports: false,
      isLoadingReportTypes: false,
      reportFields: ['#', 'name', 'recurrence', 'date_created', 'owner'],
      reportTypeFields: ['name', 'action'],
      checkedReports: [],
      isAdmin: false,
    };
  },
  created() {
    this.isAdmin = this.$store.getters.isAdmin;
    this.getReportTypes();
    this.getReports();
  },
  methods: {
    createNewReport() {
      this.creatingReport = true;
      axios.post('reports', qs.stringify(this.reportForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingReport = false;
        this.$bvModal.hide('create-new-report');
        this.initReportForm();
        this.getReports();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.creatingReport = false;
      });
    },
    refresh() {
      this.getReports();
      this.getReportTypes();
    },
    getReports() {
      this.isLoadingReports = true;
      axios.get('reports').then((response) => {
        this.reports = response.data;
        this.isLoadingReports = false;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReports = false;
      });
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
      this.reportForm.scheduled = false;
      this.reportForm.type = '';
      this.reportForm.time = '';
    },
    getReportTypes() {
      this.isLoadingReportTypes = true;
      axios.get('report-types').then((response) => {
        this.reportTypes = response.data;
        this.isLoadingReportTypes = false;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReportTypes = false;
      });
    },
    createNewReportType() {
      this.creatingReportType = true;
      axios.post('report-types', qs.stringify(this.reportTypeForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingReportType = false;
        this.$bvModal.hide('create-report-type');
        this.initReportTypeForm();
        this.getReportTypes();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.creatingReportType = false;
      });
    },
    updateReportType() {
      this.$bvModal.hide(`${this.editReportTypeForm.id}edit-report-type`);
      this.isLoadingReportTypes = true;
      axios.put('report-types', qs.stringify(this.editReportTypeForm)).then((response) => {
        const { status } = response.data;
        this.getReportTypes();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReportTypes = false;
      });
    },
    editReportType(data) {
      this.editReportTypeForm = data;
      this.$bvModal.show(`${this.editReportTypeForm.id}edit-report-type`);
    },
    deleteReportType(id) {
      this.isLoadingReportTypes = true;
      axios.delete('report-types', { params: { id } }).then((response) => {
        const { status } = response.data;
        this.getReportTypes();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.isLoadingReportTypes = false;
      });
    },
    initReportTypeForm() {
      this.reportTypeForm.sql = '';
      this.reportTypeForm.name = '';
    },
    reportTypeOptions() {
      const options = [];
      this.reportTypes.forEach((item) => {
        const option = { value: item.id, text: item.name };
        options.push(option);
      });
      return options;
    },
    downloadReport() {
      if (this.checkedReports.length === 1) {
        axios({
          url: `${this.url}/reports?action=download&report-id=${this.checkedReports[0]}`,
          method: 'GET',
          responseType: 'blob',
        })
          .then((response) => {
            const fileURL = window.URL.createObjectURL(new Blob([response.data]));
            const fileLink = document.createElement('a');
            fileLink.href = fileURL;
            fileLink.setAttribute('download', 'report.csv');
            document.body.appendChild(fileLink);
            fileLink.click();
          });
        // window.open(`${this.url}/reports?action=download&report-id=${this.checkedReports[0]}`, '_blank');
      }
    },
  },
};
</script>
