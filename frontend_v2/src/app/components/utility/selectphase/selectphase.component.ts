import { Component, OnInit, Input, Output, OnChanges } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-selectphase',
  templateUrl: './selectphase.component.html',
  styleUrls: ['./selectphase.component.scss'],
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
   * Selected phase split callback to update the router URL
   */
  @Input() selectedPhaseSplitUrlChange: any;

  /**
   * Phase selection type (radio button or select box)
   */
  @Input() phaseSelectionType: string;

  /**
   * Phase selection list type (phase or phase split)
   */
  @Input() phaseSelectionListType: string;

  /**
   * Selected phase name
   */
  phaseName = '';

  /**
   * Selected phase visibility
   */
  phaseVisibility = false;

  /**
   * Currently selected phase
   */
  selectedPhase: any = null;

  /**
   * Selected split name
   */
  splitName = '';

  /**
   * Selected phase split
   */
  selectedPhaseSplit = '';

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService, private globalService: GlobalService) {}

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
  }

  /**
   * Component on changes detected in Input.
   * @param change  changes detected
   */
  ngOnChanges(change) {}

  /**
   * Select a particular phase.
   * @param phase  phase to be selected.
   */
  selectPhase(phase) {
    this.phaseName = phase.name;
    this.phaseVisibility = phase.showPrivate;
    this.phaseSelected(phase);
  }

  /**
   * Select a particular phase split.
   * @param phaseSplit  phase split to be selected.
   * @param phaseSelectionType phase selection type (radio button or select box).
   * @param phaseSelectionListType phase selection list type (phase or phase split)
   */
  selectPhaseSplit(phaseSplit, phaseSelectionType, phaseSelectionListType) {
    this.phaseSelectionType = phaseSelectionType;
    this.phaseSelectionListType = phaseSelectionListType;
    this.selectedPhaseSplit = phaseSplit;
    this.phaseName = phaseSplit.challenge_phase_name;
    this.splitName = phaseSplit.dataset_split_name;
    this.phaseVisibility = phaseSplit.showPrivate;
    this.selectedPhaseSplitUrlChange(phaseSplit);
  }

  /**
   * Get 12Hour formatted date function.
   */
  getFormattedDate(date) {
    return this.globalService.formatDate12Hour(new Date(Date.parse(date)));
  }
}
