import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';
import { ChallengeService } from '../../../../services/challenge.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-phasecard',
  templateUrl: './phasecard.component.html',
  styleUrls: ['./phasecard.component.scss'],
})
export class PhasecardComponent implements OnInit {
  /**
   * Phase object input
   */
  @Input() phase: object;

  /**
   * start date of phase
   */
  startDate: string;

  /**
   * End date of phase
   */
  endDate: string;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * To call the API inside modal for editing the challenge phase details
   */
  apiCall: any;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    private globalService: GlobalService,
    private challengeService: ChallengeService
  ) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.updateViewElements();

    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });

    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }

  /**
   * View elements update (Called after onInit)
   */
  updateViewElements() {
    const START_DATE = new Date(Date.parse(this.phase['start_date']));
    const END_DATE = new Date(Date.parse(this.phase['end_date']));
    this.startDate = this.globalService.formatDate12Hour(START_DATE);
    this.endDate = this.globalService.formatDate12Hour(END_DATE);
  }
}
