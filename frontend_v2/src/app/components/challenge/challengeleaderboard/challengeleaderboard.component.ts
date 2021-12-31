import { Component, OnInit, QueryList, ViewChildren, AfterViewInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Router, ActivatedRoute } from '@angular/router';

// import component
import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';
import { SubmissionMetaAttributesDialogueComponent } from '../submission-meta-attributes-dialogue/submission-meta-attributes-dialogue.component';

// import service
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeleaderboard',
  templateUrl: './challengeleaderboard.component.html',
  styleUrls: ['./challengeleaderboard.component.scss'],
})
export class ChallengeleaderboardComponent implements OnInit, AfterViewInit, OnDestroy {
  /**
   * Phase select card components
   */
  @ViewChildren('phasesplitselect')
  components: QueryList<SelectphaseComponent>;

  /**
   * Leaderboard precision value
   */
  leaderboardPrecisionValue = 2;

  /**
   * Set leaderboard precision value
   */
  setLeaderboardPrecisionValue = '1.2-2';

  /**
   * Challenge phase split ID
   */
  challengePhaseSplitId;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * Has view been initialized
   */
  viewInit = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Router's public instance
   */
  routerPublic: any;

  /**
   * Phases list
   */
  phases = [];

  /**
   * Private phases list
   */
  showPrivateIds = [];

  /**
   * Phase split list
   */
  phaseSplits = [];

  /**
   * Phase splits filtered
   */
  filteredPhaseSplits = [];

  /**
   * Phase selection type (radio button or select box)
   */
  phaseSelectionType = 'selectBox';

  /**
   * Select box list type
   */
  phaseSelectionListType = 'phaseSplit';

  /**
   * Leaderboard entries list
   */
  leaderboard = [];

  /**
   * Show leaderboard updates
   */
  showLeaderboardUpdate = false;

  /**
   * Returns true if leaderboard is public for the selected phase
   */
  isSelectedPhaseLeaderboardPublic = true;

  /**
   * Currently selected phase split's id
   */
  selectedPhaseSplitId: any = null;

  /**
   * Currently selected phase split
   */
  selectedPhaseSplit: any = null;

  /**
   * Meta attribute data
   */
  metaAttributesData: any;

  /**
   * Flag for meta attribute data
   */
  showSubmissionMetaAttributesOnLeaderboard: any;

  /**
   * Current state of whether leaderboard is sorted by latest
   */
  showLeaderboardByLatest = false;

  /**
   * Current state of whether complete leaderboard
   */
  getAllEntries = false;

  /**
   * Number of entries on complete leaderboard
   */
  numberOfAllEntries = 0;

  /**
   * Current state of whether private leaderboard
   */
  showLeaderboardToggle = true;

  /**
   * Sort leaderboard based on this column
   */
  sortColumn = 'rank';

  /**
   * Text option for leadeboard sort
   */
  sortLeaderboardTextOption: string;

  /**
   * Text option for complete leadeboard
   */
  getAllEntriesTextOption = 'Include private submissions';

  /**
   * Reverse sort flag
   */
  reverseSort = false;

  /**
   * Used if leaderboard is sorted based on one of the schema labels
   */
  columnIndexSort = 0;

  /**
   * Initial rankings object
   */
  initial_ranking = {};

  /**
   * Component Class
   */
  entryHighlighted: any = null;

  /**
   * An interval for fetching the leaderboard data in every 5 seconds
   */
  pollingInterval: any;

  /**
   * Challenge phase visibility
   */
  challengePhaseVisibility = {
    owner_and_host: 1,
    host: 2,
    public: 3,
  };

  /**
   *  Highlighted row in leaderboard
   */
  highlightedEntry = null;

  /**
   * Selected order by metric name
   */
  selectedMetric: any = '';

  /**
   * Constructor.
   * @param authService  AuthService Injection.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param challengeService  ChallengeService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param endpointsService  EndPointsService Injection.
   */
  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService,
    public dialog: MatDialog
  ) {}

  /**
   * Component after view initialized.
   */
  ngAfterViewInit() {
    this.viewInit = true;
  }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
      this.filterPhases();
    });
    this.challengeService.currentPhaseSplit.subscribe((phaseSplits) => {
      this.phaseSplits = phaseSplits;
      this.filterPhases();
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }

  /**
   * Filter phases based on visibility and leaderboard public flag.
   */
  filterPhases() {
    if (this.phases.length > 0 && this.phaseSplits.length > 0) {
      for (let i = 0; i < this.phaseSplits.length; i++) {
        if (this.phaseSplits[i].visibility !== this.challengePhaseVisibility.public) {
          this.phaseSplits[i].showPrivate = true;
          this.showPrivateIds.push(this.phaseSplits[i].id);
        } else {
          this.phaseSplits[i].showPrivate = false;
        }
      }
      this.filteredPhaseSplits = this.phaseSplits;
      setTimeout(() => {
        this.checkUrlParams();
      }, 100);
    }
  }

  /**
   * Called after filtering phases to check URL for phase-split-id and highlighted-leaderboard-entry
   */
  checkUrlParams() {
    this.route.params.subscribe((params) => {
      if (params['split']) {
        this.selectedPhaseSplitId = params['split'];
        if (params.hasOwnProperty("metricName")) {
          this.selectedMetric = decodeURIComponent(params["metricName"]);
        }
        this.selectPhaseSplitId(this.selectedPhaseSplitId, this);
      }
    });
  }

  /**
   * Select a phase split from the list for a given id
   * @param id  phase split id
   * @param self  context value of this
   */
  selectPhaseSplitId(id, self) {
    let i = 0;
    for (i = 0; i < self.filteredPhaseSplits.length; i++) {
      if (parseInt(id, 10) === self.filteredPhaseSplits[i]['id']) {
        self.selectedPhaseSplit = self.filteredPhaseSplits[i];
        if (self.selectedMetric === '') {
          self.selectedMetric = self.selectedPhaseSplit.leaderboard_schema.default_order_by;
        }
        const checkViewInit = () => {
          if (self.viewInit) {
            self.components.map((item) => {
              item.selectPhaseSplitNoURLChange(self.selectedPhaseSplit, 'selectBox', 'phaseSplit');
            });
            this.phaseSplitSelected(self.selectedPhaseSplit);
          } else {
            setTimeout(() => {
              checkViewInit();
            }, 200);
          }
        };
        checkViewInit();
        break;
      }
    }
    if (i === self.filteredPhaseSplits.length) {
      self.selectedPhaseSplit = null;
    }
  }

  /**
   * This is called when a phase split is selected (from child components)
   * Updates the router URL with phase-split-id
   */
  selectedPhaseSplitUrlChange = (phaseSplit) => {
    const SELF = this;
    if (SELF.router.url.endsWith('leaderboard')) {
      SELF.router.navigate([phaseSplit['id']], { relativeTo: this.route });
    } else if (SELF.router.url.split('/').length === 5) {
      SELF.router.navigate(['../' + phaseSplit['id']], { relativeTo: this.route });
    } else if (SELF.router.url.split('/').length === 6) {
      SELF.router.navigate(['../../' + phaseSplit['id']], { relativeTo: this.route });
    }
  };

  /**
   * This is called when a metric is selected (from child components)
   * Updates the router URL with phase-split-id and  metric name
   */
   selectedMetricUrlChange = (phaseSplit, metricName) => {
    const SELF = this;
    this.selectedMetric = metricName;
    if (SELF.router.url.endsWith('leaderboard')) {
      SELF.router.navigate([phaseSplit['id'] + '/' + SELF.encodeMetricURI(metricName)], { relativeTo: this.route });
    } else if (SELF.router.url.split('/').length === 5) {
      SELF.router.navigate(['../' + phaseSplit['id'] + '/' + SELF.encodeMetricURI(metricName)], { relativeTo: this.route });
    } else if (SELF.router.url.split('/').length === 6) {
      SELF.router.navigate(['../../' + phaseSplit['id'] + '/' + SELF.encodeMetricURI(metricName)], { relativeTo: this.route });
    }
  };

  /**
   * This is called when a phase split is selected
   */
  phaseSplitSelected(phaseSplit) {
    const SELF = this;
    SELF.selectedPhaseSplit = phaseSplit;
    SELF.highlightedEntry = null;

    const API_PATH = SELF.endpointsService.particularChallengePhaseSplitUrl(SELF.selectedPhaseSplit['id']);
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.leaderboardPrecisionValue = data.leaderboard_decimal_precision;
        SELF.setLeaderboardPrecisionValue = `1.${SELF.leaderboardPrecisionValue}-${SELF.leaderboardPrecisionValue}`;
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );

    if (SELF.selectedPhaseSplit && SELF.router.url.includes('leaderboard/' + phaseSplit['id'])) {
      if (SELF.getAllEntriesTextOption === 'Exclude private submissions') {
        SELF.fetchAllEnteriesOnPublicLeaderboard(SELF.selectedPhaseSplit['id'], SELF.selectedMetric);
      } else {
        SELF.fetchLeaderboard(SELF.selectedPhaseSplit['id'], SELF.selectedMetric);
      }
      SELF.showLeaderboardByLatest = SELF.selectedPhaseSplit.show_leaderboard_by_latest_submission;
      SELF.sortLeaderboardTextOption = SELF.showLeaderboardByLatest ? 'Sort by best' : 'Sort by latest';
      const selectedPhase = SELF.phases.find((phase) => {
        return phase.id === SELF.selectedPhaseSplit.challenge_phase;
      });
      SELF.isSelectedPhaseLeaderboardPublic = selectedPhase.leaderboard_public;
    }
  }

  /**
   * This updates the leaderboard results after fetching them from API
   * @param leaderboardApi  API results for leaderboard
   * @param self  context value of this
   */
  updateLeaderboardResults(leaderboardApi, self) {
    const leaderboard = leaderboardApi.slice();
    for (let i = 0; i < leaderboard.length; i++) {
      self.initial_ranking[leaderboard[i].id] = i + 1;
      const DATE_NOW = new Date();
      const SUBMISSION_TIME = new Date(Date.parse(leaderboard[i].submission__submitted_at));
      const DURATION = self.globalService.getDateDifferenceString(DATE_NOW, SUBMISSION_TIME);
      leaderboard[i]['submission__submitted_at_formatted'] = DURATION + ' ago';
      this.showSubmissionMetaAttributesOnLeaderboard = !(leaderboard[i].submission__submission_metadata == null);
    }
    self.leaderboard = leaderboard.slice();
    self.sortLeaderboard();
    self.route.params.subscribe((params) => {
      if (params['entry']) {
        self.entryHighlighted = params['entry'];
        self.leaderboard.map((item) => {
          item['is_highlighted'] = false;
          if (self.entryHighlighted && item['submission__participant_team__team_name'] === self.entryHighlighted) {
            item['is_highlighted'] = true;
          }
        });
      }
    });
  }

  /**
   * Sort leaderboard entries wrapper
   */
  sortLeaderboard() {
    this.leaderboard = this.leaderboard.sort((obj1, obj2) => {
      const RET1 = this.sortFunction(obj1);
      const RET2 = this.sortFunction(obj2);
      if (RET1 > RET2) {
        return 1;
      }
      if (RET2 > RET1) {
        return -1;
      }
      return 0;
    });
    if (this.reverseSort) {
      this.leaderboard = this.leaderboard.reverse();
    }
  }

  /**
   * Sort function for leaderboard.
   * @param key  key for column clicked.
   */
  sortFunction(key) {
    if (this.sortColumn === 'date') {
      return Date.parse(key.submission__submitted_at);
    } else if (this.sortColumn === 'rank') {
      return this.initial_ranking[key.id];
    } else if (this.sortColumn === 'number') {
      return parseFloat(key.result[this.columnIndexSort]);
    } else if (this.sortColumn === 'string') {
      return key.submission__participant_team__team_name;
    }
    return 0;
  }

  /**
   * Sort the rank and participant team leaderboard column
   * @param sortColumn sort column ('rank' or 'string')
   */
  sortNonMetricsColumn(sortColumn) {
    const SELF = this;
    if (SELF.sortColumn === sortColumn) {
      SELF.reverseSort = !SELF.reverseSort;
    } else {
      SELF.reverseSort = false;
    }
    SELF.sortColumn = sortColumn;
    SELF.sortLeaderboard();
  }

  /**
   * To sort by the metrics column
   * @param index Schema labels index
   */
  sortMetricsColumn(index) {
    const SELF = this;
    if (SELF.sortColumn === 'number' && SELF.columnIndexSort === index) {
      SELF.reverseSort = !SELF.reverseSort;
    } else {
      SELF.reverseSort = false;
    }
    SELF.sortColumn = 'number';
    SELF.columnIndexSort = index;
    SELF.sortLeaderboard();
  }

  /**
   * Fetch leaderboard for a phase split
   * @param phaseSplitId id of the phase split
   */
  fetchLeaderboard(phaseSplitId, metricName) {
    const API_PATH = this.endpointsService.challengeLeaderboardURL(phaseSplitId, metricName);
    const SELF = this;
    SELF.showPrivateIds.forEach((id) => {
      id === phaseSplitId ? (SELF.showLeaderboardToggle = false) : (SELF.showLeaderboardToggle = true);
    });
    clearInterval(SELF.pollingInterval);
    SELF.leaderboard = [];
    SELF.showLeaderboardUpdate = false;
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.numberOfAllEntries = data['count'];
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.startLeaderboard(phaseSplitId, metricName);
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * Fetch complete leaderboard for a phase split public/private
   * @param phaseSplitId id of the phase split
   */
  fetchAllEnteriesOnPublicLeaderboard(phaseSplitId, metricName) {
    const API_PATH = this.endpointsService.challengeCompleteLeaderboardURL(phaseSplitId, metricName);
    const SELF = this;
    clearInterval(SELF.pollingInterval);
    SELF.leaderboard = [];
    SELF.showLeaderboardUpdate = false;
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.numberOfAllEntries = data['count'];
        this.challengePhaseSplitId = data.results[0].challenge_phase_split;
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.startLeaderboard(phaseSplitId, metricName);
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * function for toggeling between public leaderboard and complete leaderboard [public/private]
   */
  toggleLeaderboard(getAllEntries) {
    this.getAllEntries = getAllEntries;
    if (getAllEntries) {
      this.getAllEntriesTextOption = 'Exclude private submissions';
      this.fetchAllEnteriesOnPublicLeaderboard(this.selectedPhaseSplitId, this.selectedMetric);
    } else {
      this.getAllEntriesTextOption = 'Include private submissions';
      this.fetchLeaderboard(this.selectedPhaseSplitId, this.selectedMetric);
    }
  }

  /**
   * Call leaderboard API in the interval of 5 seconds
   * @param phaseSplitId id of the phase split
   */
  startLeaderboard(phaseSplitId, metricName) {
    let API_PATH;
    if (this.getAllEntriesTextOption === 'Exclude private submissions') {
      API_PATH = this.endpointsService.challengeCompleteLeaderboardURL(phaseSplitId, metricName);
    } else {
      API_PATH = this.endpointsService.challengeLeaderboardURL(phaseSplitId, metricName);
    }
    const SELF = this;
    clearInterval(SELF.pollingInterval);
    SELF.pollingInterval = setInterval(function () {
      SELF.apiService.getUrl(API_PATH, true, false).subscribe(
        (data) => {
          if (SELF.leaderboard.length !== data['results'].length) {
            SELF.showLeaderboardUpdate = true;
          }
        },
        (err) => {
          SELF.globalService.handleApiError(err);
        },
        () => {}
      );
    }, 5000);
  }

  /**
   * Refresh leaderboard if there is any update in data
   */
  refreshLeaderboard() {
    const API_PATH = this.endpointsService.challengeLeaderboardURL(this.selectedPhaseSplit['id'], this.selectedMetric);
    const SELF = this;
    SELF.leaderboard = [];
    SELF.showLeaderboardUpdate = false;
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.startLeaderboard(SELF.selectedPhaseSplit['id'], SELF.selectedMetric);
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  showLeaderboardByLatestOrBest() {
    const API_PATH = this.endpointsService.particularChallengePhaseSplitUrl(this.selectedPhaseSplit['id']);
    const SELF = this;
    const BODY = JSON.stringify({
      show_leaderboard_by_latest_submission: !SELF.showLeaderboardByLatest,
    });

    SELF.apiService.patchUrl(API_PATH, BODY).subscribe(
      (data) => {
        SELF.showLeaderboardByLatest = !SELF.showLeaderboardByLatest;
        SELF.sortLeaderboardTextOption = SELF.showLeaderboardByLatest ? 'Sort by best' : 'Sort by latest';
        SELF.refreshLeaderboard();
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  openDialog(metaAttribute) {
    const dialogueData = {
      width: '30%',
      data: { attribute: metaAttribute },
    };
    const dialogRef = this.dialog.open(SubmissionMetaAttributesDialogueComponent, dialogueData);
    return dialogRef.afterClosed();
  }

  /**
   *  Show dialogue box for viewing metadata
   */
  showMetaAttributesDialog(attributes) {
    const SELF = this;
    if (attributes !== false) {
      SELF.metaAttributesData = [];
      attributes.forEach(function (attribute) {
        if (attribute.type !== 'checkbox') {
          SELF.metaAttributesData.push({ name: attribute.name, value: attribute.value });
        } else {
          SELF.metaAttributesData.push({ name: attribute.name, values: attribute.values });
        }
      });
    }
    SELF.openDialog(SELF.metaAttributesData);
  }

  encodeMetricURI(metric) {
    return encodeURIComponent(metric);
  };

  /**
   * Update highlighted entry
   */
  updateHighlightedEntry(entryId) {
    const SELF = this;
    if (entryId !== null) {
      SELF.highlightedEntry = entryId;
    }
  }

  /**
   *  Fetch leaderboard metric order by flag
   */
  isMetricOrderedAscending(metric) {
    const SELF = this;
    let schema = SELF.leaderboard[0].leaderboard__schema;
    let metadata = schema.metadata;
    if (metadata != null && metadata != undefined) {
        // By default all metrics are considered higher is better
        if (metadata[metric] == undefined) {
            return false;
        }
        return metadata[metric].sort_ascending;
    }
    return false;
  };

  /**
   *  Fetch leaderboard metric description for tooltip
   */
  getLabelDescription(metric) {
      const SELF = this;
      let schema = SELF.leaderboard[0].leaderboard__schema;
      let metadata = schema.metadata;
      if (metadata != null && metadata != undefined) {
          // By default all metrics are considered higher is better
          if (metadata[metric] == undefined || metadata[metric].description == undefined) {
              return "";
          }
          return metadata[metric].description;
      }
      return "";
  };

  /**
   *  Clear the polling interval
   */
  ngOnDestroy() {
    clearInterval(this.pollingInterval);
  }
}
