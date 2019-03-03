import { Component, OnInit } from '@angular/core';

/**
 * Component Class
 */
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  /**
   * Constructor.
   */
  constructor() {}

  title = 'EvalAI|Home';

  /**
   * Component on initialized.
   */
  ngOnInit() {}
}
