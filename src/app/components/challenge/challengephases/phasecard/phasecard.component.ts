import { Component, OnInit, Input, Inject } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-phasecard',
  templateUrl: './phasecard.component.html',
  styleUrls: ['./phasecard.component.scss']
})
export class PhasecardComponent implements OnInit {

  /**
   * Phase object input
   */
  @Input() phase: object;

  /**
   * start date of phase
   */
  startDate: any;

  /**
   * End date of phase
   */
  endDate: any;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(private globalService: GlobalService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.updateViewElements();
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
