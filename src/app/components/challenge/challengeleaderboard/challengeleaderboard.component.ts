import { Component, OnInit, QueryList, ViewChildren, AfterViewInit } from '@angular/core';
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
   * Leaderboard entries list
   */
  leaderboard = [];

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
      const TEMPSPLITS = [];
      for (let i = 0; i < this.phases.length; i++) {
        if (this.phases[i]['leaderboard_public']) {
          const TEMP = this.phases[i];
          TEMP['phase_split'] = null;
          for (let j = 0; j < this.phaseSplits.length; j++) {
            if (this.phaseSplits[j]['challenge_phase'] === TEMP['id'] && this.phaseSplits[j]['visibility'] === 3) {
              const TEMP_COPY = Object.assign({}, TEMP);
              TEMP_COPY['phase_split'] = this.phaseSplits[j];
              TEMPSPLITS.push(TEMP_COPY);
            }
          }
        }
      }
      this.filteredPhaseSplits = TEMPSPLITS;
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
      console.log(params);
      if (params['split']) {
        this.selectedPhaseSplitId = params['split'];
        this.selectPhaseSplitId(this.selectedPhaseSplitId, this);
      } else {
        if (this.filteredPhaseSplits.length > 0) {
          this.router.navigate([this.filteredPhaseSplits[0]['phase_split']['id']], {relativeTo: this.route});
        }
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
      if (parseInt(id, 10) === self.filteredPhaseSplits[i]['phase_split']['id']) {
        self.selectedPhaseSplit = self.filteredPhaseSplits[i];
        const checkViewInit = () => {
          if (self.viewInit) {
            self.components.map((item) => {
              item.selectPhase(self.selectedPhaseSplit);
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
        SELF.router.navigate(['../' + phaseSplit['phase_split']['id']], {relativeTo: this.route});
      } else if (SELF.router.url.indexOf(phaseSplit['phase_split']['id']) < 0 && SELF.router.url.split('/').length === 5) {
        SELF.router.navigate(['../' + phaseSplit['phase_split']['id']], {relativeTo: this.route});
      } else if (SELF.router.url.indexOf(phaseSplit['phase_split']['id']) < 0 && SELF.router.url.split('/').length === 6) {
        SELF.router.navigate(['../../' + phaseSplit['phase_split']['id']], {relativeTo: this.route});
      } else {
        SELF.selectedPhaseSplit = phaseSplit;
        if (SELF.selectedPhaseSplit['phase_split']) {
          SELF.fetchLeaderboard(SELF.selectedPhaseSplit['phase_split']['id']);
        }
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
      } else {
        self.challengeService.currentParticipantTeams.subscribe((teams) => {
          teams.map((item) => {
            if (self.challenge && item['challenge'] && item['challenge']['id'] === self.challenge['id']) {
              self.router.navigate([item['participant_team']['team_name']], {relativeTo: this.route});
            }
          });
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
   * Fetch leaderboard for a phase split
   * @param phaseSplitId  id of the phase split
   */
  fetchLeaderboard(phaseSplitId) {
    const API_PATH = this.endpointsService.challengeLeaderboardURL(phaseSplitId);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        SELF.updateLeaderboardResults(data['results'], SELF);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        console.log('Fetched leaderboard for split:', phaseSplitId);
      }
    );
  }
}
