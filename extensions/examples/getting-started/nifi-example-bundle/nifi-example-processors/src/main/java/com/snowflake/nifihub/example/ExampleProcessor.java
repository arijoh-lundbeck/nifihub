/*
 * Copyright 2026 Snowflake Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.snowflake.nifihub.example;

import org.apache.nifi.annotation.behavior.InputRequirement;
import org.apache.nifi.annotation.documentation.CapabilityDescription;
import org.apache.nifi.annotation.documentation.Tags;
import org.apache.nifi.components.PropertyDescriptor;
import org.apache.nifi.flowfile.FlowFile;
import org.apache.nifi.processor.AbstractProcessor;
import org.apache.nifi.processor.ProcessContext;
import org.apache.nifi.processor.ProcessSession;
import org.apache.nifi.processor.Relationship;
import org.apache.nifi.processor.exception.ProcessException;
import org.apache.nifi.processor.util.StandardValidators;

import java.util.List;
import java.util.Set;

@Tags({"example", "nifihub", "template"})
@CapabilityDescription("An example processor that adds a configurable attribute to each FlowFile. "
        + "This processor serves as a template for creating new NiFi Hub processors.")
@InputRequirement(InputRequirement.Requirement.INPUT_REQUIRED)
public class ExampleProcessor extends AbstractProcessor {

    static final PropertyDescriptor ATTRIBUTE_NAME = new PropertyDescriptor.Builder()
            .name("Attribute Name")
            .displayName("Attribute Name")
            .description("The name of the attribute to add to each FlowFile.")
            .required(true)
            .addValidator(StandardValidators.NON_EMPTY_VALIDATOR)
            .build();

    static final PropertyDescriptor ATTRIBUTE_VALUE = new PropertyDescriptor.Builder()
            .name("Attribute Value")
            .displayName("Attribute Value")
            .description("The value of the attribute to add to each FlowFile. Supports Expression Language.")
            .required(true)
            .expressionLanguageSupported(org.apache.nifi.expression.ExpressionLanguageScope.FLOWFILE_ATTRIBUTES)
            .addValidator(StandardValidators.NON_EMPTY_VALIDATOR)
            .build();

    static final Relationship REL_SUCCESS = new Relationship.Builder()
            .name("success")
            .description("FlowFiles that have been successfully processed are routed to this relationship.")
            .build();

    @Override
    protected List<PropertyDescriptor> getSupportedPropertyDescriptors() {
        return List.of(ATTRIBUTE_NAME, ATTRIBUTE_VALUE);
    }

    @Override
    public Set<Relationship> getRelationships() {
        return Set.of(REL_SUCCESS);
    }

    @Override
    public void onTrigger(final ProcessContext context, final ProcessSession session) throws ProcessException {
        FlowFile flowFile = session.get();
        if (flowFile == null) {
            return;
        }

        final String attributeName = context.getProperty(ATTRIBUTE_NAME).getValue();
        final String attributeValue = context.getProperty(ATTRIBUTE_VALUE).evaluateAttributeExpressions(flowFile).getValue();

        flowFile = session.putAttribute(flowFile, attributeName, attributeValue);
        session.transfer(flowFile, REL_SUCCESS);
    }
}
