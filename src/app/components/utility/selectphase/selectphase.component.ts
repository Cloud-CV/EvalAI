import { Component, OnInit, Input, Output, OnChanges } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-selectphase',
  templateUrl: './selectphase.component.html',
  styleUrls: ['./selectphase.component.scss']
})
export class SelectphaseComponent implements OnInit, OnChanges {

  /**
   * Phase list
   */
  @Input() phases: any;

  /**
   * Selected phase callback
   */
  @Input() phaseSelected: any;

  /**
   * Phase selection type (radio button or select box)
   */
  @Input() phaseSelectionType: string;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService,
              private globalService: GlobalService) { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
    });
  }

  /**
   * Component on changes detected in Input.
   * @param change  changes detected
   */
  ngOnChanges(change) {
  }

  /**
   * Select a particular phase.
   * @param phase  phase to be selected.
   */
  selectPhase(phase) {
    this.phaseSelected(phase);
  }

  /**
   * Get 12Hour formatted date function.
   */
  getFormattedDate(date) {
    return this.globalService.formatDate12Hour(new Date(Date.parse(date)));
  }

}
