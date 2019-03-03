import { Component, OnInit } from '@angular/core';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-get-involved',
  templateUrl: './get-involved.component.html',
  styleUrls: ['./get-involved.component.scss']
})
export class GetInvolvedComponent implements OnInit {

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(private globalService: GlobalService) { }
  description = 'Thanks for your interest in helping out with the EvalAI\
  project! We\'re a team of volunteers around the world who want to\
  reduce the barrier to entry for doing AI research and make it easier\
  for researchers, students and developers to develop and use state-of-the-art\
  algorithms as a service. We are always listening for suggestions to improve our\
  platform, including identifying bugs and discussing enhancements.\
  Here are different ways in which how you can help:';

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.globalService.scrollToTop();
  }

}
