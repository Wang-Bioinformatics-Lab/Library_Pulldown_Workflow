#!/usr/bin/env nextflow
nextflow.enable.dsl=2

//This publish dir is mostly  useful when we want to import modules in other workflows, keep it here usually don't change it
params.publishdir = "$launchDir/output"
TOOL_FOLDER = "$moduleDir/bin"
MODULES_FOLDER = "$TOOL_FOLDER/NextflowModules"


// COMPATIBILITY NOTE: The following might be necessary if this workflow is being deployed in a slightly different environemnt
// checking if outdir is defined,
// if so, then set publishdir to outdir
if (params.outdir) {
    _publishdir = params.outdir
}
else{
    _publishdir = params.publishdir
}

// Augmenting with nf_output
_publishdir = "${_publishdir}"

process determineGNPSLibraries {
    /* This is a sample process that runs a python script.

    For each process, you can specify the publishDir, which is the directory where the output files will be saved.
    You can also specify the conda environment that will be used to run the process.
    The input and output blocks define the input and output files for the process.
    The script block contains the command that will be run in the process.
    */

    publishDir "$_publishdir", mode: 'copy'

    conda "$TOOL_FOLDER/conda_env.yml"

    input:
    val x 

    output:
    file 'library_summaries/*'

    script:
    """
    mkdir -p library_summaries
    python $TOOL_FOLDER/process_gnps_libraries.py library_summaries
    """
}

process formatGNPSLibraries {
    /* This is a sample process that formats the GNPS libraries.

    The input and output blocks define the input and output files for the process.
    The script block contains the command that will be run in the process.
    */

    publishDir "$_publishdir", mode: 'copy'

    conda "$TOOL_FOLDER/conda_rdkit.yml"

    maxForks 4

    input:
    file "input/*"

    output:
    file '*.json' optional true
    file '*.msp' optional true
    file '*.mgf' optional true

    script:
    """
    python $TOOL_FOLDER/format_gnps_libraries.py input/* . 
    """
}

process createAggregrateGNPSLibraries {
    publishDir "$_publishdir", mode: 'copy'

    conda "$TOOL_FOLDER/conda_env.yml"

    input:
    file "input/*"
    file "input/*"
    file "input/*"

    output:
    file '*.json'
    file '*.msp'
    file '*.mgf'

    script:
    """
    python $TOOL_FOLDER/create_aggregate_gnps_libraries.py input .
    """
}

workflow Main{
    // -------  -------
    /* 
    For each named workflow, add 'take' and 'main' blocks.

    --take--
    For the take block, you can specify the input parameters that will be passed to the workflow.
    Another option instead of passing all the values, is to use a map, which is a dictionary of key-value pairs.

    --main--
    The main block is where the workflow is defined. You can call other processes and workflows from here.

    --emit--
    This is an optional block and if you are new to nextflow you can ignore it.
    This is can be useful in future generations of nextflow, replacing the need for the 'publishDir' directive.
    */

    take: 
    input_map

    main:
    val_ch = 0
    gnpslibrary_summary_json_ch = determineGNPSLibraries(val_ch)

    // Now we will do some formatting
    (gnps_library_formats_json_ch, gnps_library_formats_msp_ch, gnps_library_formats_mgf_ch) = formatGNPSLibraries(gnpslibrary_summary_json_ch.flatten())

    // lets aggregate
    createAggregrateGNPSLibraries(gnps_library_formats_json_ch.collect(), gnps_library_formats_msp_ch.collect(), gnps_library_formats_mgf_ch.collect())

    emit:
    py_out = determineGNPSLibraries.out
}

workflow {
    /* 
    The input map is created to reduce the dependency of the other workflows to the `params`
    */
    input_map = []
    out = Main(input_map)
}
