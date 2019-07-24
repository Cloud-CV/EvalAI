import { Component, OnInit, QueryList, ViewChildren, AfterViewInit, Self } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router, ActivatedRoute } from '@angular/router';
import { SelectphaseComponent } from '../../utility/selectphase/selectphase.component';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeleaderboard',
  templateUrl: './challengeleaderboard.component.html',
  styleUrls: ['./challengeleaderboard.component.scss']
})
export class ChallengeleaderboardComponent implements OnInit, AfterViewInit {

  /**
   * Phase select card components
   */
  @ViewChildren('phasesplitselect')
  components: QueryList<SelectphaseComponent>;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

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
   * Currently selected phase split's id
   */
  selectedPhaseSplitId: any = null;

  /**
   * Currently selected phase split
   */
  selectedPhaseSplit: any = null;

  /**
   * Sort leaderboard based on this column
   */
  sortColumn = 'rank';

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
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService, private apiService: ApiService,
              private endpointsService: EndpointsService) { }

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
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
    });
    this.challengeService.currentPhases.subscribe(
      phases => {
        this.phases = phases;
        this.filterPhases();
    });
    this.challengeService.currentPhaseSplit.subscribe(
      phaseSplits => {
        this.phaseSplits = phaseSplits;
        this.filterPhases();
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
    this.route.params.subscribe(params => {
      if (params['split']) {
        this.selectedPhaseSplitId = params['split'];
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
        const checkViewInit = () => {
          if (self.viewInit) {
            self.components.map((item) => {
              item.selectPhaseSplit(self.selectedPhaseSplit, 'selectBox', 'phaseSplit');
            });
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
   */
  phaseSplitSelected() {
    const SELF = this;
    return (phaseSplit) => {
      if (SELF.router.url.endsWith('leaderboard')) {
        SELF.router.navigate([phaseSplit['id']], {relativeTo: this.route});
      } else if (SELF.router.url.split('/').length === 5) {
        SELF.router.navigate(['../' + phaseSplit['id']], {relativeTo: this.route});
      } else if (SELF.router.url.split('/').length === 6) {
        SELF.router.navigate(['../../' + phaseSplit['id']], {relativeTo: this.route});
      }
      SELF.selectedPhaseSplit = phaseSplit;
      if (SELF.selectedPhaseSplit) {
        SELF.fetchLeaderboard(SELF.selectedPhaseSplit['id']);
      }
    };

  }

  /**
   * This updates the leaderboard results after fetching them from API
   * @param leaderboardApi  API results for leaderboard
   * @param self  context value of this
   */
  updateLeaderboardResults(leaderboardApi, self) {
    const leaderboard = leaderboardApi.slice();
    for (let i = 0; i < leaderboard.length; i++) {
      self.initial_ranking[leaderboard[i].submission__participant_team__team_name] = i + 1;
      const DATE_NOW = new Date();
      const SUBMISSION_TIME = new Date(Date.parse(leaderboard[i].submission__submitted_at));
      const DURATION = self.globalService.getDateDifferenceString(DATE_NOW, SUBMISSION_TIME);
      leaderboard[i]['submission__submitted_at_formatted'] = DURATION + ' ago';
    }
    self.leaderboard = leaderboard.slice();
    self.sortLeaderboard();
    self.route.params.subscribe(params => {
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
      return this.initial_ranking[key.submission__participant_team__team_name];
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
  sortNonMetricsColumn (sortColumn) {
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
  sortMetricsColumn (index) {
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
  fetchLeaderboard(phaseSplitId) {
    const API_PATH = this.endpointsService.challengeLeaderboardURL(phaseSplitId);
    const SELF = this;
    clearInterval(SELF.pollingInterval);
    SELF.leaderboard = [];
    SELF.showLeaderboardUpdate = false;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.startLeaderboard(phaseSplitId);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * Call leaderboard API in the interval of 5 seconds
   * @param phaseSplitId id of the phase split
   */
  startLeaderboard(phaseSplitId) {
    const API_PATH = this.endpointsService.challengeLeaderboardURL(phaseSplitId);
    const SELF = this;
    clearInterval(SELF.pollingInterval);
    SELF.pollingInterval = setInterval(function() {
      SELF.apiService.getUrl(API_PATH, true, false).subscribe(
        data => {
          if (SELF.leaderboard.length !== data['results'].length) {
            SELF.showLeaderboardUpdate = true;
          }
        },
        err => {
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
    const API_PATH = this.endpointsService.challengeLeaderboardURL(this.selectedPhaseSplit['id']);
    const SELF = this;
    SELF.leaderboard = [];
    SELF.showLeaderboardUpdate = false;
    SELF.apiService.getUrl(API_PATH).subscribe(
      data => {
        SELF.updateLeaderboardResults(data['results'], SELF);
        SELF.startLeaderboard(SELF.selectedPhaseSplit['id']);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }
}
