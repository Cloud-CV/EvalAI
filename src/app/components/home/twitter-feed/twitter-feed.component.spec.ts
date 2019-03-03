import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TwitterFeedComponent } from './twitter-feed.component';
import { WindowService } from '../../../services/window.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('TwitterFeedComponent', () => {
  let component: TwitterFeedComponent;
  let fixture: ComponentFixture<TwitterFeedComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TwitterFeedComponent ],
      providers: [ WindowService ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TwitterFeedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
